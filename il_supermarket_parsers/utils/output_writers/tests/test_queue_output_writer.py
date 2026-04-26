import queue
import unittest

from il_supermarket_parsers.utils.output_writers.queue_output_writer import (
    ParsedRowsQueue,
    QueueOutputWriter,
)
from il_supermarket_parsers.utils.types import FileCompleteMessage


class TestQueueOutputWriter(unittest.IsolatedAsyncioTestCase):
    """Unit tests for QueueOutputWriter (real in-memory queue, no mocks)."""

    def setUp(self) -> None:
        self._q = queue.Queue()
        self._writer = QueueOutputWriter(self._q)

    def _drain(self) -> list:
        items = []
        while not self._q.empty():
            items.append(self._q.get_nowait())
        return items

    async def test_initialize_is_noop(self) -> None:
        await self._writer.initialize()
        self.assertTrue(self._q.empty())

    async def test_initialize_new_file_is_noop(self) -> None:
        await self._writer. (None)  # type: ignore[arg-type]
        self.assertTrue(self._q.empty())

    async def test_write_row_enqueues_dict(self) -> None:
        await self._writer.write_row({"a": 1})
        self.assertEqual(self._drain(), [{"a": 1}])

    async def test_write_multiple_rows_order_preserved(self) -> None:
        rows = [{"id": 0}, {"id": 1}, {"id": 2}]
        for row in rows:
            await self._writer.write_row(row)
        self.assertEqual(self._drain(), rows)

    async def test_write_file_complete_enqueues_model_dump(self) -> None:
        msg = FileCompleteMessage(
            file_name="x.xml",
            total_expected_records=5,
        )
        await self._writer.write_file_complete(msg)
        items = self._drain()
        self.assertEqual(len(items), 1)
        self.assertEqual(
            items[0],
            {"file_complete": "true", "file_name": "x.xml", "total_expected_records": 5},
        )

    async def test_close_puts_none_sentinel(self) -> None:
        await self._writer.write_row({"a": 1})
        await self._writer.write_row({"b": 2})
        self._writer.close()

        parsed_queue = ParsedRowsQueue(self._q)
        messages = list(parsed_queue.get_all_messages())
        self.assertEqual(messages, [{"a": 1}, {"b": 2}])

    def test_exists_always_true(self) -> None:
        self.assertTrue(self._writer.exists())

    def test_get_path_returns_memory_queue(self) -> None:
        self.assertEqual(self._writer.get_path(), "memory_queue")

    def test_get_existing_columns_returns_empty(self) -> None:
        self.assertEqual(self._writer.get_existing_columns(), [])


if __name__ == "__main__":
    unittest.main()
