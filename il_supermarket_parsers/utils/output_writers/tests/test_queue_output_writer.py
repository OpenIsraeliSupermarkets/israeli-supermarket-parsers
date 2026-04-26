"""Unit tests for QueueOutputWriter."""

import multiprocessing
import queue
import unittest

from il_supermarket_parsers.utils.output_writers.queue_output_writer import (
    ParsedRowsQueue,
    QueueOutputWriter,
    create_queue_pair,
)
from il_supermarket_parsers.utils.types import FileCompleteMessage


def _worker(writer: QueueOutputWriter, rows: list) -> None:
    """Write rows from a subprocess then close the stream."""
    import asyncio  # pylint: disable=import-outside-toplevel

    async def _run():
        for row in rows:
            await writer.write_row(row)
        writer.close()

    asyncio.run(_run())


class TestQueueOutputWriter(unittest.IsolatedAsyncioTestCase):
    """Unit tests for QueueOutputWriter (real in-memory queue, no mocks)."""

    def setUp(self) -> None:
        """Set up the test environment."""
        self._q = queue.Queue()
        self._writer = QueueOutputWriter(self._q)

    def _drain(self) -> list:
        """Drain the queue and return the items."""
        items = []
        while not self._q.empty():
            items.append(self._q.get_nowait())
        return items

    async def test_initialize_is_noop(self) -> None:
        """Test that the initialize method is a no-op."""
        await self._writer.initialize()
        self.assertTrue(self._q.empty())

    async def test_initialize_new_file_is_noop(self) -> None:
        """Test that the initialize_new_file method is a no-op."""
        await self._writer.initialize_new_file(None)  # type: ignore[arg-type]
        self.assertTrue(self._q.empty())

    async def test_write_row_enqueues_dict(self) -> None:
        """Test that the write_row method enqueues a dictionary."""
        await self._writer.write_row({"a": 1})
        self.assertEqual(self._drain(), [{"a": 1}])

    async def test_write_multiple_rows_order_preserved(self) -> None:
        """Test that the write_row method enqueues rows in the order they are written."""
        rows = [{"id": 0}, {"id": 1}, {"id": 2}]
        for row in rows:
            await self._writer.write_row(row)
        self.assertEqual(self._drain(), rows)

    async def test_write_file_complete_enqueues_model_dump(self) -> None:
        """Test that the write_file_complete method enqueues the FileCompleteMessage model dump."""
        msg = FileCompleteMessage(
            file_name="x.xml",
            total_expected_records=5,
        )
        await self._writer.write_file_complete(msg)
        items = self._drain()
        self.assertEqual(len(items), 1)
        self.assertEqual(
            items[0],
            {
                "file_complete": "true",
                "file_name": "x.xml",
                "total_expected_records": 5,
            },
        )

    async def test_close_puts_none_sentinel(self) -> None:
        """Test that the close method puts a None sentinel into the queue."""
        await self._writer.write_row({"a": 1})
        await self._writer.write_row({"b": 2})
        self._writer.close()

        parsed_queue = ParsedRowsQueue(self._q)
        messages = list(parsed_queue.get_all_messages())
        self.assertEqual(messages, [{"a": 1}, {"b": 2}])

    def test_exists_always_true(self) -> None:
        """Test that the exists method returns True."""
        self.assertTrue(self._writer.exists())

    def test_get_path_returns_memory_queue(self) -> None:
        """Test that the get_path method returns "memory_queue"."""
        self.assertEqual(self._writer.get_path(), "memory_queue")

    def test_get_existing_columns_returns_empty(self) -> None:
        """Test that the get_existing_columns method returns an empty list."""
        self.assertEqual(self._writer.get_existing_columns(), [])

    # ------------------------------------------------------------------
    # cross-process usage via create_queue_pair
    # ------------------------------------------------------------------

    def test_create_queue_pair_returns_writer_and_reader(self) -> None:
        """Test that the create_queue_pair method returns a writer and a reader."""
        writer, reader = create_queue_pair()
        self.assertIsInstance(writer, QueueOutputWriter)
        self.assertIsInstance(reader, ParsedRowsQueue)

    def test_create_queue_pair_cross_process(self) -> None:
        """Writer passed to a subprocess; parent reads all rows via the reader."""
        rows = [{"id": 0}, {"id": 1}, {"id": 2}]
        writer, reader = create_queue_pair()

        p = multiprocessing.Process(target=_worker, args=(writer, rows))
        p.start()
        received = list(reader.get_all_messages())
        p.join(timeout=10)

        self.assertEqual(p.exitcode, 0)
        self.assertEqual(received, rows)


if __name__ == "__main__":
    unittest.main()
