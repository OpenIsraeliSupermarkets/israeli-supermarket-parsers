"""Unit tests for KafkaOutputWriter."""

from unittest.mock import MagicMock, patch
import unittest
from il_supermarket_parsers.utils.output_writers.kafka_output_writer import (
    KafkaOutputWriter,
)


_PATCH_TARGET = (
    "il_supermarket_parsers.utils.output_writers.kafka_output_writer.KafkaProducer"
)


def _make_writer(mock_producer_cls, **kwargs):
    """Construct a KafkaOutputWriter with sensible defaults."""
    mock_producer_cls.return_value = MagicMock()
    defaults = {
        "bootstrap_servers": ["host:9092"],
        "enabled_scraper": "shufersal",
        "enabled_file_type": "pricefull",
    }
    defaults.update(kwargs)
    writer = KafkaOutputWriter(**defaults)
    return writer, mock_producer_cls.return_value


class TestKafkaOutputWriter(unittest.IsolatedAsyncioTestCase):
    """Unit tests for KafkaOutputWriter (KafkaProducer fully mocked)."""

    def setUp(self) -> None:
        self._patcher = patch(_PATCH_TARGET)
        self._mock_producer_cls = self._patcher.start()
        self._writer, self._mock_producer = _make_writer(self._mock_producer_cls)
        self._configure_send()

    def _configure_send(self) -> None:
        """Make producer.send(...).get(timeout=...) succeed by default."""
        future = MagicMock()
        future.get.return_value = None
        self._mock_producer.send.return_value = future

    def tearDown(self) -> None:
        self._patcher.stop()

    # ------------------------------------------------------------------
    # initialize / lifecycle
    # ------------------------------------------------------------------

    async def test_initialize_sets_initialized_flag(self) -> None:
        """Test that the initialize method sets the initialized flag."""
        self.assertFalse(self._writer._initialized)  # pylint: disable=protected-access
        await self._writer.initialize()
        self.assertTrue(self._writer._initialized)  # pylint: disable=protected-access

    async def test_initialize_is_idempotent(self) -> None:
        """Test that the initialize method is idempotent."""
        await self._writer.initialize()
        await self._writer.initialize()
        self.assertTrue(self._writer._initialized)  # pylint: disable=protected-access

    async def test_initialize_new_file_resets_columns(self) -> None:
        """Test that the initialize_new_file method resets the existing columns."""
        await self._writer.write_row({"a": 1, "b": 2})
        self.assertGreater(
            len(self._writer._existing_columns), 0  # pylint: disable=protected-access
        )
        await self._writer.initialize_new_file(None)  # type: ignore[arg-type]
        self.assertEqual(
            self._writer._existing_columns, []  # pylint: disable=protected-access
        )

    # ------------------------------------------------------------------
    # topic rendering
    # ------------------------------------------------------------------

    def test_topic_default_template(self) -> None:
        """Test that the topic method returns the default template."""
        self.assertEqual(self._writer.topic, "shufersal_pricefull")

    def test_topic_custom_template(self) -> None:
        """Test that the topic method returns the custom template."""
        _, _ = _make_writer(
            self._mock_producer_cls,
            topic_template="raw_{enabled_file_type}",
        )

        self._mock_producer_cls.return_value = MagicMock()
        writer = KafkaOutputWriter(
            bootstrap_servers=["host:9092"],
            enabled_scraper="shufersal",
            enabled_file_type="pricefull",
            topic_template="raw_{enabled_file_type}",
        )
        self.assertEqual(writer.topic, "raw_pricefull")

    # ------------------------------------------------------------------
    # get_path / exists / get_existing_columns
    # ------------------------------------------------------------------

    def test_get_path_includes_broker_and_topic(self) -> None:
        """Test that the get_path method includes the broker and topic."""
        self.assertEqual(
            self._writer.get_path(), "kafka://host:9092/shufersal_pricefull"
        )

    def test_exists_false_when_no_columns(self) -> None:
        """Test that the exists method returns False when no columns are present."""
        self.assertFalse(self._writer.exists())

    async def test_exists_true_after_write(self) -> None:
        """Test that the exists method returns True after writing a row."""
        await self._writer.write_row({"x": 1})
        self.assertTrue(self._writer.exists())

    def test_get_existing_columns_returns_copy(self) -> None:
        """Test that the get_existing_columns method returns a copy of the existing columns."""
        cols = self._writer.get_existing_columns()
        cols.append("injected")
        self.assertEqual(
            self._writer._existing_columns, []  # pylint: disable=protected-access
        )

    # ------------------------------------------------------------------
    # write_row — message sending
    # ------------------------------------------------------------------

    async def test_write_row_sends_message(self) -> None:
        """Test that the write_row method sends a message."""
        await self._writer.write_row({"a": 1})
        self._mock_producer.send.assert_called_once()
        call_kwargs = self._mock_producer.send.call_args
        self.assertEqual(
            call_kwargs.kwargs.get("value") or call_kwargs[1].get("value"), {"a": 1}
        )

    async def test_write_row_schema_alignment(self) -> None:
        """Test that the write_row method aligns the schema of the messages."""
        await self._writer.write_row({"a": 1})
        await self._writer.write_row({"a": 2, "b": 3})

        calls = self._mock_producer.send.call_args_list
        self.assertEqual(len(calls), 2)

        first_value = calls[0].kwargs.get("value") or calls[0][1].get("value")
        second_value = calls[1].kwargs.get("value") or calls[1][1].get("value")

        # After second write, existing columns = ["a", "b"] (sorted union)
        # First row only had "a"; second row adds "b"
        self.assertEqual(first_value, {"a": 1})
        # Second row is aligned with all known columns
        self.assertIn("a", second_value)
        self.assertIn("b", second_value)
        self.assertEqual(second_value["a"], 2)
        self.assertEqual(second_value["b"], 3)

    async def test_write_row_schema_alignment_with_missing_columns(self) -> None:
        """Test that the write_row method aligns the schema of the messages with missing columns."""
        await self._writer.write_row({"a": 2, "b": 3})
        await self._writer.write_row({"a": 1})

        calls = self._mock_producer.send.call_args_list
        self.assertEqual(len(calls), 2)

        first_value = calls[0].kwargs.get("value") or calls[0][1].get("value")
        second_value = calls[1].kwargs.get("value") or calls[1][1].get("value")

        # After second write, existing columns = ["a", "b"] (sorted union)
        # First row only had "a"; second row adds "b"
        self.assertEqual(second_value["a"], 1)
        self.assertEqual(second_value["b"], None)
        # Second row is aligned with all known columns
        self.assertIn("a", first_value)
        self.assertIn("b", first_value)
        self.assertEqual(first_value["a"], 2)
        self.assertEqual(first_value["b"], 3)

    # ------------------------------------------------------------------
    # close
    # ------------------------------------------------------------------

    def test_close_calls_producer_close(self) -> None:
        """Test that the close method calls the producer close method."""
        self._writer.close()
        self._mock_producer.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
