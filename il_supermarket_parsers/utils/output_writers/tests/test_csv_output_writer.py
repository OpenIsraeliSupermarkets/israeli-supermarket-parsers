"""Unit tests for CSVOutputWriter."""

# pylint: disable=missing-function-docstring,protected-access

from __future__ import annotations

import csv
import json
import os
import tempfile
import unittest
from unittest import mock

import pandas as pd

from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)
from il_supermarket_parsers.utils.csv_reader import read_data_rows


class TestCSVOutputWriter(unittest.IsolatedAsyncioTestCase):
    """Integration tests for CSVOutputWriter (real files, no mocks)."""

    def setUp(self) -> None:
        # Closed in tearDown; not using context manager to keep path on self.
        self._tmpdir = (
            tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        )
        self._output_folder = self._tmpdir.name

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _new_writer(self, reduce_duplicates: bool = True) -> CSVOutputWriter:
        return CSVOutputWriter(
            output_folder=self._output_folder,
            csv_file_name="pricefull_shufersal",
            reduce_duplicates=reduce_duplicates,
        )

    def _csv_path(self) -> str:
        return os.path.join(self._output_folder, "pricefull_shufersal.csv")

    async def test_initialize_sets_initialized_flag(self) -> None:
        """Test that the initialized flag is set correctly."""
        writer = self._new_writer()
        self.assertFalse(writer._initialized)
        self.assertFalse(writer._header_written)
        await writer.initialize()
        self.assertTrue(writer._initialized)
        self.assertFalse(writer._header_written)

    async def test_initialize_reads_existing_file_columns(self) -> None:
        """Test that existing file columns are read correctly."""
        with open(self._csv_path(), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["x", "y", "z"])
            w.writerow([1, 2, 3])
        writer = self._new_writer()
        await writer.initialize()
        self.assertEqual(
            writer._existing_columns,
            ["x", "y", "z"],
        )
        self.assertTrue(writer._header_written)

    async def test_initialize_is_idempotent(self) -> None:
        writer = self._new_writer()
        await writer.initialize()
        await writer.initialize()
        self.assertTrue(writer._initialized)

    async def test_write_row_content(self) -> None:
        writer = self._new_writer()
        await writer.write_row({"name": "foo", "value": 42})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], {"name": "foo", "value": "42"})

    async def test_nested_dict_round_trips_as_json_in_cell(self) -> None:
        """Nested row values must be valid JSON in CSV for downstream validation."""
        writer = self._new_writer(reduce_duplicates=False)
        nested = {
            "item": [
                {"itemcode": "123", "minqty": "1"},
                {"itemcode": "456", "minqty": "2"},
            ]
        }
        await writer.write_row({"id": 1, "groups": nested})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "1")
        parsed = json.loads(rows[0]["groups"])
        self.assertEqual(parsed, nested)

    async def test_nested_dict_round_trips_as_json_in_cell_duplicate(self) -> None:
        """Nested row values must be valid JSON in CSV for downstream validation."""
        writer = self._new_writer(reduce_duplicates=True)
        nested = {
            "item": [
                {"itemcode": "123", "minqty": "1"},
                {"itemcode": "456", "minqty": "2"},
            ]
        }
        await writer.write_row({"id": 1, "groups": nested})
        await writer.write_row({"id": 2, "groups": nested})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], "1")
        parsed = json.loads(rows[0]["groups"])
        self.assertEqual(parsed, nested)

        self.assertEqual(rows[1]["id"], "2")
        self.assertTrue(pd.isna(rows[1]["groups"]))

        rows = read_data_rows(self._csv_path(), ffill=True)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], "1")
        parsed = json.loads(rows[0]["groups"])
        self.assertEqual(parsed, nested)

        self.assertEqual(rows[1]["id"], "2")
        parsed = json.loads(rows[1]["groups"])
        self.assertEqual(parsed, nested)

    async def test_write_multiple_rows_same_schema(self) -> None:
        """Test that multiple rows with the same schema are written correctly."""
        writer = self._new_writer()
        for i in range(3):
            await writer.write_row({"id": i, "k": f"v{i}"})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], {"id": "0", "k": "v0"})
        self.assertEqual(rows[1], {"id": "1", "k": "v1"})
        self.assertEqual(rows[2], {"id": "2", "k": "v2"})

    async def test_schema_evolution_adds_new_column(self) -> None:
        """Test that a new column is added when it is not present in a row."""
        writer = self._new_writer()
        await writer.write_row({"a": 1})
        await writer.write_row({"a": 2, "b": 3})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": CSVOutputWriter.EMPTY_STRING})
        self.assertEqual(rows[1], {"a": "2", "b": "3"})

    async def test_schema_evolution_removes_column(self) -> None:
        """Test that a column is removed when it is not present in a row."""
        writer = self._new_writer()
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_row({"a": 1})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})

        self.assertTrue(pd.isna(rows[1]["a"]))
        self.assertEqual(rows[1]["b"], CSVOutputWriter.EMPTY_STRING)

    async def test_reduce_duplicates_nullifies_repeated_value(self) -> None:
        """Test that repeated values are nullified when reduce_duplicates is True."""
        writer = self._new_writer(reduce_duplicates=True)
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_row({"a": 1, "b": 3})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})
        # Dedup-masked cells are written as empty CSV cells, which read back as NaN.
        self.assertTrue(pd.isna(rows[1]["a"]))
        self.assertEqual(rows[1]["b"], "3")

        rows = read_data_rows(self._csv_path(), ffill=True)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})
        self.assertEqual(rows[1], {"a": "1", "b": "3"})

    async def test_no_reduce_duplicates_preserves_all_values(self) -> None:
        """Test that deduplication is not performed when reduce_duplicates is False."""
        writer = self._new_writer(reduce_duplicates=False)
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_row({"a": 1, "b": 3})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path(), ffill=False)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})
        self.assertEqual(rows[1], {"a": "1", "b": "3"})

    async def test_no_dedup_across_files(self) -> None:
        """Test that deduplication is not carried across files."""
        writer = self._new_writer(reduce_duplicates=True)
        await writer.initialize_new_file(None)  # type: ignore[arg-type]
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        await writer.initialize_new_file(None)  # type: ignore[arg-type]
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})
        self.assertEqual(
            rows[1],
            {"a": "1", "b": "2"},
            "second logical file must not inherit dedup from the first",
        )

    async def test_no_dedup_across_files_different_order(self) -> None:
        """Test that deduplication is not carried across files."""
        writer = self._new_writer(reduce_duplicates=True)
        await writer.initialize_new_file(None)  # type: ignore[arg-type]
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        await writer.initialize_new_file(None)  # type: ignore[arg-type]
        await writer.write_row({"b": 2, "a": 1})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})
        self.assertEqual(
            rows[1],
            {"a": "1", "b": "2"},
            "second logical file must not inherit dedup from the first",
        )

    async def test_output_csv_content_snapshot(self) -> None:
        """Full snapshot of the raw CSV bytes produced by a realistic write sequence."""
        writer = self._new_writer(reduce_duplicates=True)

        # file 1: two rows, second row adds a new column
        await writer.initialize_new_file(None)  # type: ignore[arg-type]
        await writer.write_row(
            {"chain_id": "7290027600007", "item_code": "1001", "price": "5.90"}
        )
        await writer.write_row(
            {
                "chain_id": "7290027600007",
                "item_code": "1002",
                "price": "3.50",
                "unit": "kg",
            }
        )
        await writer.write_file_complete(None)  # type: ignore[arg-type]

        # file 2: dedup boundary resets; repeated chain_id should appear again
        await writer.initialize_new_file(None)  # type: ignore[arg-type]
        await writer.write_row(
            {
                "chain_id": "7290027600007",
                "item_code": "2001",
                "price": "9.99",
                "unit": "l",
            }
        )
        await writer.write_row(
            {
                "chain_id": "7290027600007",
                "item_code": "2001",
                "price": "9.99",
                "unit": "l",
            }
        )
        await writer.write_file_complete(None)  # type: ignore[arg-type]

        with open(self._csv_path(), "r", encoding="utf-8") as f:
            actual = f.read()

        expected = (
            "chain_id,item_code,price,unit\n"
            "7290027600007,1001,5.90,''\n"  # first row; unit col not yet present → ''
            ",1002,3.50,kg\n"  # chain_id deduped (same as previous row)
            "7290027600007,2001,9.99,l\n"  # new file → dedup reset, chain_id reappears
            ",,,\n"  # all four values identical → all deduped to empty
        )
        self.assertEqual(actual, expected)

    async def test_source_empty_value_written_as_empty_cell(self) -> None:
        """A genuinely empty tag value from source XML (e.g. <City></City>) is written
        as an empty CSV cell and reads back as NaN, distinct from the EMPTY_STRING
        sentinel used for schema-evolution gaps."""
        writer = self._new_writer(reduce_duplicates=True)
        await writer.write_row({"chain_id": "1", "city": "TLV"})
        await writer.write_row(
            {"chain_id": "2", "city": ""}
        )  # source XML: <City></City>
        await writer.write_row({"chain_id": "3", "city": "HFA"})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = read_data_rows(self._csv_path(), ffill=True)
        self.assertEqual(rows[0]["city"], "TLV")
        # Empty-string source value lands as an empty cell → NaN after read_csv.

        self.assertEqual(rows[1]["city"], CSVOutputWriter.EMPTY_STRING)
        self.assertEqual(rows[2]["city"], "HFA")

    async def test_source_empty_value_is_indistinguishable_from_rle_masked_value(
        self,
    ) -> None:
        """Documents the RLE-vs-source-empty ambiguity.

        Row 2 is RLE-masked (same city as row 1) and row 3 has a genuinely
        empty city from the source XML.  Both land as NaN in the CSV, so a
        naive ffill over the file recovers the RLE loss in row 2 correctly but
        incorrectly propagates "8300" into row 3, which should stay empty.
        """
        writer = self._new_writer(reduce_duplicates=True)
        await writer.write_row({"chain_id": "1", "city": "8300"})
        await writer.write_row({"chain_id": "2", "city": "8300"})  # RLE-masked
        await writer.write_row({"chain_id": "3", "city": ""})  # source-empty
        await writer.write_file_complete(None)  # type: ignore[arg-type]

        rows = read_data_rows(self._csv_path(), ffill=True)
        self.assertEqual(rows[0], {"chain_id": "1", "city": "8300"})
        self.assertEqual(rows[1], {"chain_id": "2", "city": "8300"})
        self.assertEqual(
            rows[2], {"chain_id": "3", "city": CSVOutputWriter.EMPTY_STRING}
        )

    async def test_literal_null_text_is_not_ffilled_from_previous_row(self) -> None:
        """XML text 'null' must survive CSV+ffill; pandas default NA would NaN it."""
        writer = self._new_writer(reduce_duplicates=True)
        await writer.write_row({"item_code": "1", "unit": "רשת"})
        await writer.write_row({"item_code": "2", "unit": "null"})
        await writer.write_file_complete(None)  # type: ignore[arg-type]

        rows = read_data_rows(self._csv_path(), ffill=True)
        self.assertEqual(rows[0]["unit"], "רשת")
        self.assertEqual(rows[1]["unit"], "null")

    async def test_none_value_is_not_ffilled_from_previous_row(self) -> None:
        """Missing XML text (None) must use the empty sentinel, not RLE/ffill."""
        writer = self._new_writer(reduce_duplicates=True)
        await writer.write_row({"item_code": "1", "remarks": "keep me"})
        await writer.write_row({"item_code": "2", "remarks": None})
        await writer.write_row({"item_code": "3", "remarks": float("nan")})
        await writer.write_file_complete(None)  # type: ignore[arg-type]

        rows = read_data_rows(self._csv_path(), ffill=True)
        self.assertEqual(rows[0]["remarks"], "keep me")
        self.assertEqual(rows[1]["remarks"], CSVOutputWriter.EMPTY_STRING)
        self.assertEqual(rows[2]["remarks"], CSVOutputWriter.EMPTY_STRING)

    def _temp_artifacts(self) -> list[str]:
        """Return leftover rewrite temp filenames in the output folder."""
        names = []
        for name in os.listdir(self._output_folder):
            if name.endswith("_temp.csv") or name.endswith(".csv.tmp"):
                names.append(name)
            elif name.startswith(".") and ".csv" in name:
                # mkstemp prefix=`.{csv_file_name}.` + suffix=`.csv.tmp`
                names.append(name)
        return sorted(names)

    async def test_schema_evolution_leaves_no_temp_csv(self) -> None:
        """Successful column rewrite must not leave durable temp files."""
        writer = self._new_writer()
        await writer.initialize_new_file(None)  # type: ignore[arg-type]
        await writer.write_row({"a": 1})
        await writer.write_file_complete(None)  # type: ignore[arg-type]

        await writer.initialize_new_file(None)  # type: ignore[arg-type]
        await writer.write_row({"a": 2, "b": 3})
        await writer.write_file_complete(None)  # type: ignore[arg-type]

        self.assertEqual(self._temp_artifacts(), [])
        self.assertTrue(os.path.exists(self._csv_path()))
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": CSVOutputWriter.EMPTY_STRING})
        self.assertEqual(rows[1], {"a": "2", "b": "3"})

    async def test_append_columns_cleans_temp_on_interrupt(self) -> None:
        """If rewrite fails mid-flight, no temp artifact may remain."""
        writer = self._new_writer()
        await writer.write_row({"a": 1})
        await writer.write_file_complete(None)  # type: ignore[arg-type]

        with mock.patch(
            "il_supermarket_parsers.utils.output_writers.csv_output_writer.os.replace",
            side_effect=OSError("simulated interrupt"),
        ):
            with self.assertRaises(OSError):
                writer._append_columns_to_csv_sync(["b"])

        self.assertEqual(self._temp_artifacts(), [])
        # Original file must still be intact after a failed rewrite.
        rows = read_data_rows(self._csv_path())
        self.assertEqual(rows, [{"a": "1"}])

    async def test_initialize_removes_legacy_stale_temp_csv(self) -> None:
        """Init deletes leftover `*_temp.csv` from older interrupted rewrites."""
        legacy_temp = self._csv_path().replace(".csv", "_temp.csv")
        with open(legacy_temp, "w", encoding="utf-8") as f:
            f.write("stale\n")
        self.assertTrue(os.path.exists(legacy_temp))

        writer = self._new_writer()
        await writer.initialize()
        self.assertFalse(os.path.exists(legacy_temp))
        self.assertEqual(self._temp_artifacts(), [])


    async def test_stale_temp_file_cleaned_on_init(self) -> None:
        """Test that stale temp files from previous crashes are cleaned up on init."""
        # Create a stale temp file
        temp_path = self._csv_path().replace(".csv", "_temp.csv")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write("stale,data\n")
        self.assertTrue(os.path.exists(temp_path))

        writer = self._new_writer()
        await writer.initialize()

        # Temp file should be removed
        self.assertFalse(os.path.exists(temp_path))

    async def test_temp_file_cleaned_on_column_rewrite_exception(self) -> None:
        """Test that temp file is cleaned up if column rewrite fails mid-write."""
        # Create initial CSV
        with open(self._csv_path(), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["a", "b"])
            w.writerow(["1", "2"])

        writer = self._new_writer()
        await writer.initialize()

        temp_path = writer._get_temp_path()

        # Patch os.replace to simulate failure after temp file is written
        original_replace = os.replace

        def failing_replace(src, dst):
            raise OSError("Simulated failure")

        os.replace = failing_replace
        try:
            with self.assertRaises(OSError):
                writer._append_columns_to_csv_sync(["c"])
            # Temp file should be cleaned up even on failure
            self.assertFalse(os.path.exists(temp_path))
        finally:
            os.replace = original_replace

    async def test_no_temp_file_after_successful_column_rewrite(self) -> None:
        """Test that no temp file remains after successful column rewrite."""
        # Create initial CSV
        with open(self._csv_path(), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["a", "b"])
            w.writerow(["1", "2"])

        writer = self._new_writer()
        await writer.initialize()

        temp_path = writer._get_temp_path()

        writer._append_columns_to_csv_sync(["c"])

        # No temp file should remain
        self.assertFalse(os.path.exists(temp_path))
        # Original file should exist with new columns
        self.assertTrue(os.path.exists(self._csv_path()))
        rows = read_data_rows(self._csv_path())
        self.assertEqual(len(rows), 1)
        self.assertIn("c", rows[0])

    async def test_column_rewrite_atomic_replace(self) -> None:
        """Test that column rewrite uses atomic replace (original content preserved on failure)."""
        original_content = "a,b\n1,2\n"
        with open(self._csv_path(), "w", encoding="utf-8") as f:
            f.write(original_content)

        writer = self._new_writer()
        await writer.initialize()

        # Patch os.replace to simulate failure
        original_replace = os.replace

        def failing_replace(src, dst):
            raise OSError("Simulated failure")

        os.replace = failing_replace
        try:
            with self.assertRaises(OSError):
                writer._append_columns_to_csv_sync(["c"])
            # Original file should be preserved
            with open(self._csv_path(), "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), original_content)
        finally:
            os.replace = original_replace


if __name__ == "__main__":
    unittest.main()
