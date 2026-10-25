"""Caps for routed file queues and parsed-row queues, and Manager death."""

import asyncio
import json
import logging
import multiprocessing
import os
import tempfile
import threading
import time
import unittest

from il_supermarket_scarper.utils.databases import JsonDataBase

from il_supermarket_parsers.raw_parsing_pipeline import RawParsingPipeline
from il_supermarket_parsers.task import ConvertingTask, ConvertingTaskConfig
from il_supermarket_parsers.tests.test_queue_routing import (
    MockAsyncQueueHandler,
    MockQueueWrapper,
    make_queue_message,
)
from il_supermarket_parsers.utils.data_loaders.queue_data_loader import QueueDataLoader
from il_supermarket_parsers.utils.data_loaders.queue_router import (
    QueueManagerConnectionError,
    QueueRouter,
    RoutedQueueHandler,
    RoutedQueueWrapper,
)
from il_supermarket_parsers.utils.logger import Logger
from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)
from il_supermarket_parsers.utils.output_writers.queue_output_writer import (
    ParsedRowsQueue,
    QueueOutputWriter,
)
from il_supermarket_parsers.utils.status.parser_status import ParserStatus

# Tests read the Manager queue objects held by the handlers.
# pylint: disable=protected-access

PRICEFULL_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290027600007</ChainId>
  <SubChainId>1</SubChainId>
  <StoreId>001</StoreId>
  <BikoretNo>0</BikoretNo>
  <Items>
    <Item>
      <ItemCode>1001</ItemCode>
      <ItemType>0</ItemType>
      <ItemName>Milk 3%</ItemName>
      <ItemPrice>6.90</ItemPrice>
    </Item>
  </Items>
</Root>
"""


class _LogCapture(logging.Handler):
    """Collect log records emitted during a test."""

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def _watch_qsize(managed_queue):
    """Record the high-water mark of a Manager queue until stopped."""
    state = {"n": 0, "stop": threading.Event()}

    def _run():
        while not state["stop"].is_set():
            try:
                state["n"] = max(state["n"], managed_queue.qsize())
            except (EOFError, BrokenPipeError, OSError):
                break
            time.sleep(0.005)

    threading.Thread(target=_run, daemon=True).start()
    return state


def _wait_until_full(managed_queue, maxsize, timeout=5):
    """Block until the queue reaches its cap and has not grown past it."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        size = managed_queue.qsize()
        if size >= maxsize:
            if size > maxsize:
                raise AssertionError(f"queue size {size} exceeded {maxsize}")
            return
        time.sleep(0.01)
    raise AssertionError(
        f"queue size stayed at {managed_queue.qsize()}, expected {maxsize}"
    )


async def _drain_routed(handler):
    """Read a routed queue slowly so the producer stays blocked on the cap."""
    received = []
    async for msg in handler.queue_handler.get_all_messages():
        received.append(msg["file_name"])
        await asyncio.sleep(0.02)
    return received


class TestBoundedQueues(unittest.TestCase):
    """Routed files and parsed rows respect a small queue cap."""

    def test_defaults_leave_queues_unbounded(self):
        """Zero, the default, still accepts a burst with no consumer."""
        config = ConvertingTaskConfig(
            source_configuration={"folder": "dumps"},
            output_configuration=[{"output_mode": "csv", "output_folder": "outputs"}],
            status_configuration={"database_type": "json", "base_path": "outputs"},
        )
        self.assertEqual(config.max_queue_size, 0)
        self.assertEqual(config.max_output_queue_size, 0)

        messages = [
            make_queue_message("PRICE_FILE", "7290700100008", index)
            for index in range(5)
        ]
        router = QueueRouter(
            "SHUFERSAL",
            MockQueueWrapper(MockAsyncQueueHandler(messages)),
            ["PRICE_FILE"],
        )
        router.start()
        self.assertTrue(router.wait(timeout=5))
        self.assertEqual(router._routed_queues["PRICE_FILE"].qsize(), 6)

    def test_slow_consumer_receives_every_file_and_row_within_cap(self):
        """A slow consumer gets every file and row, and neither queue grows past its cap."""
        self._assert_routed_files_stay_within_cap()
        self._assert_output_rows_stay_within_cap()

    def _assert_routed_files_stay_within_cap(self):
        maxsize = 2
        count = 5
        messages = [
            make_queue_message("PRICE_FILE", "7290700100008", index)
            for index in range(count)
        ]
        with tempfile.TemporaryDirectory() as root:
            task = ConvertingTask(
                enabled_parsers=["SHUFERSAL"],
                files_types=["PRICE_FILE"],
                source_configuration={
                    "queue_handlers": {
                        "SHUFERSAL": MockQueueWrapper(MockAsyncQueueHandler(messages))
                    }
                },
                output_configuration=[{"output_mode": "csv", "output_folder": root}],
                status_configuration={"database_type": "json", "base_path": root},
                max_queue_size=maxsize,
            )
            task.runner._setup_queue_routing()
            handler = task.runner._routed_handlers["SHUFERSAL"]["PRICE_FILE"]
            routed = handler.queue_handler._queue
            peak = _watch_qsize(routed)
            try:
                _wait_until_full(routed, maxsize)
                time.sleep(0.3)
                self.assertEqual(routed.qsize(), maxsize)
                received = asyncio.run(_drain_routed(handler))
            finally:
                peak["stop"].set()
            self.assertEqual(len(received), count)
            self.assertEqual(peak["n"], maxsize)
            self.assertTrue(task.runner._routers["SHUFERSAL"].wait(timeout=5))

    def _assert_output_rows_stay_within_cap(self):
        maxsize = 2
        rows = [{"id": index} for index in range(5)]
        with tempfile.TemporaryDirectory() as root:
            task = ConvertingTask(
                enabled_parsers=["SHUFERSAL"],
                files_types=["PRICE_FILE"],
                source_configuration={"folder": root},
                output_configuration=[{"output_mode": "queue", "queue_type": "memory"}],
                status_configuration={"database_type": "json", "base_path": root},
                max_output_queue_size=maxsize,
            )
            managed_queue = task._output_queues[("SHUFERSAL", "PRICE_FILE")]
            writer = QueueOutputWriter(managed_queue)

            def _produce():
                async def _run():
                    for row in rows:
                        await writer.write_row(row)
                    await writer.close()

                asyncio.run(_run())

            producer = threading.Thread(target=_produce)
            peak = _watch_qsize(managed_queue)
            producer.start()
            try:
                _wait_until_full(managed_queue, maxsize)
                time.sleep(0.3)
                self.assertEqual(managed_queue.qsize(), maxsize)
                received = []
                for row in ParsedRowsQueue(managed_queue).get_all_messages():
                    received.append(row)
                    time.sleep(0.02)
            finally:
                peak["stop"].set()
                producer.join(timeout=5)
            self.assertFalse(producer.is_alive())
            self.assertEqual(received, rows)
            self.assertEqual(peak["n"], maxsize)


class TestManagerDeath(unittest.IsolatedAsyncioTestCase):
    """A dead Manager is a failed file-type job, not a normal empty stream."""

    async def test_killing_manager_mid_stream_fails_status(self):
        """ERROR is logged and the job status has had_errors after the Manager dies."""
        manager = multiprocessing.Manager()
        killed = False
        capture = _LogCapture()
        Logger.logger.addHandler(capture)
        try:
            managed_queue = manager.Queue()
            handler = RoutedQueueWrapper(
                RoutedQueueHandler(managed_queue, "SHUFERSAL", "PRICE_FULL_FILE")
            )
            with tempfile.TemporaryDirectory() as root:
                status_name = "shufersal_price_full_file"
                pipeline = RawParsingPipeline(
                    data_loader=QueueDataLoader({"SHUFERSAL": handler}),
                    output_writer=CSVOutputWriter(root, status_name),
                    parser_status=ParserStatus(
                        JsonDataBase(status_name, base_path=root)
                    ),
                )
                managed_queue.put(
                    {
                        "file_name": "PriceFull7290027600007-001-20250101.xml",
                        "file_content": PRICEFULL_XML.encode("utf-8"),
                        "file_link": "http://example.com/price.xml",
                        "metadata": {},
                    }
                )
                status_path = os.path.join(root, f"{status_name}.json")
                killer_error = {}

                def _kill_after_first_file():
                    deadline = time.time() + 15
                    while time.time() < deadline:
                        if os.path.exists(status_path):
                            try:
                                with open(status_path, "r", encoding="utf-8") as handle:
                                    data = json.load(handle)
                            except (json.JSONDecodeError, OSError):
                                time.sleep(0.05)
                                continue
                            events = data.get("events") or []
                            if any(
                                event.get("status") == "processed" for event in events
                            ):
                                manager._process.kill()  # pylint: disable=no-member
                                return
                        time.sleep(0.05)
                    killer_error["error"] = AssertionError(
                        "parsed file was not recorded before the Manager was killed"
                    )

                killer = threading.Thread(target=_kill_after_first_file, daemon=True)
                killer.start()
                with self.assertRaises(QueueManagerConnectionError):
                    await asyncio.wait_for(
                        pipeline.process("SHUFERSAL", "PRICE_FULL_FILE"),
                        timeout=20,
                    )
                killed = True
                killer.join(timeout=5)
                if "error" in killer_error:
                    raise killer_error["error"]

                with open(status_path, "r", encoding="utf-8") as handle:
                    status = json.load(handle)
                completed = [
                    event
                    for event in status["global_status"]
                    if event["status"] == "completed"
                ]
                self.assertEqual(len(completed), 1)
                self.assertTrue(completed[0]["had_errors"])
                self.assertGreaterEqual(completed[0]["total_files"], 1)

                errors = [
                    record.getMessage()
                    for record in capture.records
                    if record.levelno >= logging.ERROR
                ]
                self.assertTrue(
                    any("Manager connection" in message for message in errors),
                    errors,
                )
                infos = [
                    record.getMessage()
                    for record in capture.records
                    if record.levelno == logging.INFO
                ]
                self.assertFalse(
                    any(message.startswith("Finished consuming") for message in infos),
                    infos,
                )
        finally:
            Logger.logger.removeHandler(capture)
            if not killed:
                manager.shutdown()


if __name__ == "__main__":
    unittest.main()
