"""Unit tests for MongoOutputWriter."""

from unittest.mock import MagicMock, patch
import unittest

from il_supermarket_parsers.utils.output_writers.mongo_output_writer import (
    MongoOutputWriter,
)

_PATCH_TARGET = (
    "il_supermarket_parsers.utils.output_writers.mongo_output_writer.MongoClient"
)


def _make_writer(mock_client_cls, **kwargs):
    """Construct MongoOutputWriter with MongoClient mocked."""
    mock_collection = MagicMock()
    mock_db = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    mock_client = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_client_cls.return_value = mock_client

    defaults = {
        "connection_url": "mongodb://localhost:27017",
        "db_name": "supermarket",
        "collection_name": "shufersal_pricefull",
    }
    defaults.update(kwargs)
    writer = MongoOutputWriter(**defaults)
    return writer, mock_client, mock_collection


class TestMongoOutputWriter(unittest.IsolatedAsyncioTestCase):
    """MongoOutputWriter tests (MongoClient fully mocked)."""

    def setUp(self) -> None:
        self._patcher = patch(_PATCH_TARGET)
        self._mock_client_cls = self._patcher.start()
        self._writer, self._mock_client, self._mock_collection = _make_writer(
            self._mock_client_cls
        )

    def tearDown(self) -> None:
        self._patcher.stop()

    async def test_initialize_sets_initialized_flag(self) -> None:
        self.assertFalse(self._writer._initialized)  # pylint: disable=protected-access
        await self._writer.initialize()
        self.assertTrue(self._writer._initialized)  # pylint: disable=protected-access

    async def test_initialize_new_file_resets_columns(self) -> None:
        await self._writer.write_row({"a": 1, "b": 2})
        self.assertGreater(
            len(self._writer._existing_columns), 0  # pylint: disable=protected-access
        )
        await self._writer.initialize_new_file(None)  # type: ignore[arg-type]
        self.assertEqual(
            self._writer._existing_columns, []  # pylint: disable=protected-access
        )

    def test_get_path_includes_db_and_collection(self) -> None:
        self.assertEqual(
            self._writer.get_path(),
            "mongodb:///supermarket/shufersal_pricefull",
        )

    def test_exists_false_when_no_columns(self) -> None:
        self.assertFalse(self._writer.exists())

    async def test_exists_true_after_write(self) -> None:
        await self._writer.write_row({"x": 1})
        self.assertTrue(self._writer.exists())

    def test_get_existing_columns_returns_copy(self) -> None:
        cols = self._writer.get_existing_columns()
        cols.append("injected")
        self.assertEqual(
            self._writer._existing_columns, []  # pylint: disable=protected-access
        )

    async def test_write_row_inserts_document(self) -> None:
        await self._writer.write_row({"a": 1})
        self._mock_collection.insert_one.assert_called_once_with({"a": 1})

    async def test_write_row_schema_alignment(self) -> None:
        await self._writer.write_row({"a": 1})
        await self._writer.write_row({"a": 2, "b": 3})

        calls = self._mock_collection.insert_one.call_args_list
        self.assertEqual(len(calls), 2)

        first_doc = calls[0][0][0]
        second_doc = calls[1][0][0]

        self.assertEqual(first_doc, {"a": 1})
        self.assertEqual(second_doc["a"], 2)
        self.assertEqual(second_doc["b"], 3)

    async def test_write_row_schema_alignment_with_missing_columns(self) -> None:
        await self._writer.write_row({"a": 2, "b": 3})
        await self._writer.write_row({"a": 1})

        calls = self._mock_collection.insert_one.call_args_list
        second_doc = calls[1][0][0]

        self.assertEqual(second_doc["a"], 1)
        self.assertIsNone(second_doc["b"])

    async def test_close_calls_client_close(self) -> None:
        await self._writer.close()
        self._mock_client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
