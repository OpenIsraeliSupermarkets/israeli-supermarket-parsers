"""Queue-mode caps (worker inboxes, parsed-row queues) and Manager death."""

import asyncio
import json
import logging
import multiprocessing
import os
import tempfile
import threading
import time
import unittest
from collections import Counter

from il_supermarket_scarper.utils.databases import JsonDataBase

from il_supermarket_parsers.queue_worker import run_queue_worker
from il_supermarket_parsers.raw_parsing_pipeline import RawParsingPipeline
from il_supermarket_parsers.task import ConvertingTask, ConvertingTaskConfig
from il_supermarket_parsers.utils.data_loaders.queue_data_loader import QueueDataLoader
from il_supermarket_parsers.utils.data_loaders.queue_router import (
    QueueManagerConnectionError,
    QueueRouter,
    RoutedQueueHandler,
    RoutedQueueWrapper,
    WorkerDispatcher,
)
from il_supermarket_parsers.utils.logger import Logger
from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)
from il_supermarket_parsers.utils.status.parser_status import ParserStatus
from il_supermarket_parsers.utils.types import (
    CsvOutputConfiguration,
    JsonStatusConfiguration,
)

# Tests read the Manager queues held by the task and the dispatcher.
# pylint: disable=protected-access

PRICEFULL_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <ChainId>7290027600007</ChainId>
  <SubChainId>1</SubChainId>
  <StoreId>001</StoreId>
  <BikoretNo>0</BikoretNo>
  <Items>
    <Item><ItemCode>1001</ItemCode><ItemName>Milk 3%</ItemName></Item>
    <Item><ItemCode>1002</ItemCode><ItemName>Bread</ItemName></Item>
  </Items>
</Root>
"""

STORES_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Root>
  <CHAINID>7290027600007</CHAINID>
  <LASTUPDATEDATE>2025-01-01</LASTUPDATEDATE>
  <STORES>
    <STORE><STOREID>001</STOREID><STORENAME>Main Branch</STORENAME></STORE>
    <STORE><STOREID>002</STOREID><STORENAME>Second Branch</STORENAME></STORE>
  </STORES>
</Root>
"""

CHAIN_ID = "7290027600007"
PAIR_FILES = {
    "PRICE_FILE": [f"Price{CHAIN_ID}-001-2025010100{i:02d}.xml" for i in range(4)],
    "PRICE_FULL_FILE": [
        f"PriceFull{CHAIN_ID}-001-2025010101{i:02d}.xml" for i in range(3)
    ],
    "STORE_FILE": [f"Stores{CHAIN_ID}-000-202501010200.xml"],
}
ROWS_PER_FILE = 2


def _message(file_name: str) -> dict:
    content = STORES_XML if file_name.startswith("Stores") else PRICEFULL_XML
    return {
        "file_name": file_name,
        "file_content": content.encode("utf-8"),
        "file_link": f"http://example.com/{file_name}",
        "metadata": {},
    }


def _interleaved_messages() -> list:
    """Every price file first, then the store file, as in the review's repro."""
    names = (
        PAIR_FILES["PRICE_FILE"]
        + PAIR_FILES["PRICE_FULL_FILE"]
        + PAIR_FILES["STORE_FILE"]
    )
    return [_message(name) for name in names]


class _ListQueueHandler:
    """Scraper-queue stand-in that yields a fixed list of messages."""

    def __init__(self, messages: list):
        self._messages = list(messages)

    async def get_all_messages(self):
        """Yield every message, then end the stream."""
        for message in self._messages:
            yield message

    async def close(self):
        """Nothing to re-publish."""


class _ScraperQueue:
    """Matches ``scraper.consume()`` values: the handler is on ``queue_handler``."""

    def __init__(self, handler):
        self.queue_handler = handler


class _LogCapture(logging.Handler):
    """Collect log records emitted during a test."""

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


class _PeakSize:
    """Track the largest qsize seen across a set of Manager queues."""

    def __init__(self):
        self.peak = 0
        self._queues = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def watch(self, queues):
        """Start sampling these queues."""
        self._queues = list(queues)

    def _run(self):
        while not self._stop.is_set():
            for managed_queue in self._queues:
                try:
                    self.peak = max(self.peak, managed_queue.qsize())
                except (EOFError, BrokenPipeError, OSError):
                    return
            time.sleep(0.002)

    def stop(self):
        """Stop sampling."""
        self._stop.set()
        self._thread.join(timeout=2)


def _drain_slowly(rows_queue, sink: list) -> None:
    for message in rows_queue.get_all_messages():
        sink.append(message)
        time.sleep(0.01)


def _completed_status(status_path: str) -> list:
    with open(status_path, "r", encoding="utf-8") as handle:
        status = json.load(handle)
    return [
        event for event in status["global_status"] if event["status"] == "completed"
    ]


class TestQueueCapDefaults(unittest.TestCase):
    """Zero, the default, keeps every queue unbounded."""

    def test_defaults_are_unbounded(self):
        """Both caps default to 0 and a 0-cap inbox takes a burst with no reader."""
        config = ConvertingTaskConfig(
            source_configuration={"folder": "dumps"},
            output_configuration=[{"output_mode": "csv", "output_folder": "outputs"}],
            status_configuration={"database_type": "json", "base_path": "outputs"},
        )
        self.assertEqual(config.max_queue_size, 0)
        self.assertEqual(config.max_output_queue_size, 0)

        dispatcher = WorkerDispatcher(1, ["SHUFERSAL"], ["PRICE_FILE"])
        for name in PAIR_FILES["PRICE_FILE"]:
            dispatcher.dispatch("SHUFERSAL", "PRICE_FILE", _message(name))
        self.assertEqual(dispatcher.inboxes[0].qsize(), len(PAIR_FILES["PRICE_FILE"]))


class TestCappedQueueMode(unittest.TestCase):
    """Small caps, more pairs than workers, and slow readers."""

    def test_all_files_and_rows_arrive_within_caps(self):
        """No pair stalls behind another, and no queue grows past its cap.

        Three pairs share two workers. The router sees every price file before
        the store file, so a cap that blocked on an unscheduled pair would
        never deliver the store file or finish.
        """
        inbox_cap = 1
        output_cap = 2
        with tempfile.TemporaryDirectory() as root:
            task = ConvertingTask(
                enabled_parsers=["SHUFERSAL"],
                files_types=list(PAIR_FILES),
                multiprocessing=2,
                source_configuration={
                    "queue_handlers": {
                        "SHUFERSAL": _ScraperQueue(
                            _ListQueueHandler(_interleaved_messages())
                        )
                    }
                },
                output_configuration=[
                    {"output_mode": "queue", "queue_type": "memory"},
                ],
                status_configuration={"database_type": "json", "base_path": root},
                max_queue_size=inbox_cap,
                max_output_queue_size=output_cap,
            )
            output_queues = task.consume()
            received = {key: [] for key in output_queues}
            readers = [
                threading.Thread(
                    target=_drain_slowly, args=(rows_queue, received[key]), daemon=True
                )
                for key, rows_queue in output_queues.items()
            ]
            output_peak = _PeakSize()
            output_peak.watch(task._output_queues.values())
            for reader in readers:
                reader.start()

            inbox_peak = _PeakSize()
            task.start()
            deadline = time.time() + 10
            while task.runner._dispatcher is None and time.time() < deadline:
                time.sleep(0.005)
            self.assertIsNotNone(task.runner._dispatcher, "routing never started")
            inbox_peak.watch(task.runner._dispatcher.inboxes)

            task._thread.join(timeout=60)
            stalled = task._thread.is_alive()
            for reader in readers:
                reader.join(timeout=10)
            inbox_peak.stop()
            output_peak.stop()
            self.assertFalse(stalled, "parsing stalled with capped queues")
            self._assert_every_pair_complete(root, received)
            self.assertLessEqual(inbox_peak.peak, inbox_cap)
            self.assertLessEqual(output_peak.peak, output_cap)

    def _assert_every_pair_complete(self, root: str, received: dict) -> None:
        for file_type, names in PAIR_FILES.items():
            messages = received[("SHUFERSAL", file_type)]
            rows = Counter(
                message["file_name"]
                for message in messages
                if "file_complete" not in message
            )
            completes = [
                message["file_name"]
                for message in messages
                if "file_complete" in message
            ]
            self.assertEqual(sorted(completes), sorted(names), file_type)
            self.assertEqual(rows, {name: ROWS_PER_FILE for name in names}, file_type)

            completed = _completed_status(
                os.path.join(root, f"shufersal_{file_type.lower()}.json")
            )
            self.assertEqual(len(completed), 1, file_type)
            self.assertFalse(completed[0]["had_errors"], file_type)
            self.assertEqual(completed[0]["total_files"], len(names), file_type)

    def test_pairs_without_files_still_complete(self):
        """A pair that never gets a file still records a completed status."""
        with tempfile.TemporaryDirectory() as root:
            task = ConvertingTask(
                enabled_parsers=["SHUFERSAL", "VICTORY"],
                files_types=["PRICE_FILE"],
                multiprocessing=1,
                source_configuration={
                    "queue_handlers": {
                        "SHUFERSAL": _ScraperQueue(_ListQueueHandler([]))
                    }
                },
                output_configuration=[{"output_mode": "csv", "output_folder": root}],
                status_configuration={"database_type": "json", "base_path": root},
                max_queue_size=1,
            )
            task.start()
            task._thread.join(timeout=60)
            self.assertFalse(task._thread.is_alive())
            for name in ("shufersal_price_file", "victory_price_file"):
                completed = _completed_status(os.path.join(root, f"{name}.json"))
                self.assertEqual(len(completed), 1, name)
                self.assertEqual(completed[0]["total_files"], 0, name)

    def test_router_failure_marks_pairs_failed(self):
        """A scraper queue that breaks mid-stream fails its pairs instead of passing."""

        class _BrokenHandler:
            async def get_all_messages(self):
                """Yield one file, then fail like a dead scraper Manager."""
                yield _message(PAIR_FILES["PRICE_FILE"][0])
                raise BrokenPipeError("scraper queue gone")

            async def close(self):
                """Nothing to re-publish."""

        dispatcher = WorkerDispatcher(1, ["SHUFERSAL"], ["PRICE_FILE"], 1)
        router = QueueRouter(
            "SHUFERSAL",
            _ScraperQueue(_BrokenHandler()),
            ["PRICE_FILE"],
            dispatcher=dispatcher,
        )
        router.start()
        inbox = dispatcher.inboxes[0]
        self.assertEqual(inbox.get(timeout=5)["kind"], "file")
        end = inbox.get(timeout=5)
        self.assertEqual(end["kind"], "end")
        self.assertIn("scraper queue gone", end["error"])
        self.assertTrue(router.wait(timeout=5))


class TestManagerDeath(unittest.IsolatedAsyncioTestCase):
    """A dead Manager is a failed file-type job, not a normal empty stream."""

    async def asyncSetUp(self):
        self.capture = _LogCapture()
        Logger.logger.addHandler(self.capture)

    async def asyncTearDown(self):
        Logger.logger.removeHandler(self.capture)

    def _error_messages(self) -> list:
        return [
            record.getMessage()
            for record in self.capture.records
            if record.levelno >= logging.ERROR
        ]

    @staticmethod
    def _kill_after_processed(manager, status_path: str, failures: dict):
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                with open(status_path, "r", encoding="utf-8") as handle:
                    events = json.load(handle).get("events") or []
            except (OSError, json.JSONDecodeError):
                events = []
            if any(event.get("status") == "processed" for event in events):
                manager._process.kill()  # pylint: disable=no-member
                return
            time.sleep(0.05)
        failures["error"] = AssertionError("file was never processed")

    async def test_worker_inbox_manager_death_fails_status(self):
        """Killing the inbox Manager mid-stream logs ERROR and fails the open pair."""
        manager = multiprocessing.Manager()
        killed = False
        try:
            inbox = manager.Queue()
            inbox.put(
                {
                    "kind": "file",
                    "parser_name": "SHUFERSAL",
                    "file_type": "PRICE_FULL_FILE",
                    "message": _message(PAIR_FILES["PRICE_FULL_FILE"][0]),
                }
            )
            with tempfile.TemporaryDirectory() as root:
                status_path = os.path.join(root, "shufersal_price_full_file.json")
                failures = {}
                killer = threading.Thread(
                    target=self._kill_after_processed,
                    args=(manager, status_path, failures),
                    daemon=True,
                )
                killer.start()
                with self.assertRaises(QueueManagerConnectionError):
                    await asyncio.wait_for(
                        asyncio.to_thread(
                            asyncio.run,
                            run_queue_worker(
                                inbox=inbox,
                                output_configuration=[
                                    CsvOutputConfiguration(
                                        output_mode="csv", output_folder=root
                                    )
                                ],
                                status_configuration=JsonStatusConfiguration(
                                    database_type="json", base_path=root
                                ),
                            ),
                        ),
                        timeout=20,
                    )
                killed = True
                killer.join(timeout=5)
                if "error" in failures:
                    raise failures["error"]

                completed = _completed_status(status_path)
                self.assertEqual(len(completed), 1)
                self.assertTrue(completed[0]["had_errors"])
                self.assertEqual(completed[0]["total_files"], 1)
                self.assertTrue(
                    any("Manager connection" in m for m in self._error_messages()),
                    self._error_messages(),
                )
        finally:
            if not killed:
                manager.shutdown()

    async def test_routed_queue_manager_death_fails_status(self):
        """The per-file-type routed queue path also fails instead of reporting 0 files."""
        manager = multiprocessing.Manager()
        killed = False
        try:
            managed_queue = manager.Queue()
            handler = RoutedQueueWrapper(
                RoutedQueueHandler(managed_queue, "SHUFERSAL", "PRICE_FULL_FILE")
            )
            managed_queue.put(_message(PAIR_FILES["PRICE_FULL_FILE"][0]))
            with tempfile.TemporaryDirectory() as root:
                status_name = "shufersal_price_full_file"
                status_path = os.path.join(root, f"{status_name}.json")
                pipeline = RawParsingPipeline(
                    data_loader=QueueDataLoader({"SHUFERSAL": handler}),
                    output_writer=CSVOutputWriter(root, status_name),
                    parser_status=ParserStatus(
                        JsonDataBase(status_name, base_path=root)
                    ),
                )
                failures = {}
                killer = threading.Thread(
                    target=self._kill_after_processed,
                    args=(manager, status_path, failures),
                    daemon=True,
                )
                killer.start()
                with self.assertRaises(QueueManagerConnectionError):
                    await asyncio.wait_for(
                        pipeline.process("SHUFERSAL", "PRICE_FULL_FILE"), timeout=20
                    )
                killed = True
                killer.join(timeout=5)
                if "error" in failures:
                    raise failures["error"]

                completed = _completed_status(status_path)
                self.assertEqual(len(completed), 1)
                self.assertTrue(completed[0]["had_errors"])
                self.assertTrue(
                    any("Manager connection" in m for m in self._error_messages()),
                    self._error_messages(),
                )
                self.assertFalse(
                    any(
                        record.getMessage().startswith("Finished consuming")
                        for record in self.capture.records
                    )
                )
        finally:
            if not killed:
                manager.shutdown()


if __name__ == "__main__":
    unittest.main()
