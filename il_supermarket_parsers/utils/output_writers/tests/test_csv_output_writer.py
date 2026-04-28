"""Unit tests for CSVOutputWriter."""

# pylint: disable=missing-function-docstring,protected-access

from __future__ import annotations

import csv
import json
import os
import tempfile
import unittest

import pandas as pd

from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)


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
            self._output_folder,
            "shufersal",
            "pricefull",
            reduce_duplicates=reduce_duplicates,
        )

    def _csv_path(self) -> str:
        return os.path.join(self._output_folder, "pricefull_shufersal.csv")

    def _read_data_rows(self, ffill=False) -> list[dict[str, str | None]]:
        """Read data rows from the CSV file."""
        df = pd.read_csv(self._csv_path(), dtype=str)
        if ffill:
            df = df.ffill()
        return df.to_dict(orient="records")

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
        rows = self._read_data_rows()
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
        rows = self._read_data_rows()
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
        rows = self._read_data_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], "1")
        parsed = json.loads(rows[0]["groups"])
        self.assertEqual(parsed, nested)

        self.assertEqual(rows[1]["id"], "2")
        self.assertTrue(pd.isna(rows[1]["groups"]))

        rows = self._read_data_rows(ffill=True)
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
        rows = self._read_data_rows()
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
        rows = self._read_data_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": CSVOutputWriter.EMPTY_STRING})
        self.assertEqual(rows[1], {"a": "2", "b": "3"})

    async def test_schema_evolution_removes_column(self) -> None:
        """Test that a column is removed when it is not present in a row."""
        writer = self._new_writer()
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_row({"a": 1})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = self._read_data_rows()
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
        rows = self._read_data_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})
        # Dedup-masked cells are written as empty CSV cells, which read back as NaN.
        self.assertTrue(pd.isna(rows[1]["a"]))
        self.assertEqual(rows[1]["b"], "3")

        rows = self._read_data_rows(ffill=True)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})
        self.assertEqual(rows[1], {"a": "1", "b": "3"})

    async def test_no_reduce_duplicates_preserves_all_values(self) -> None:
        """Test that deduplication is not performed when reduce_duplicates is False."""
        writer = self._new_writer(reduce_duplicates=False)
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_row({"a": 1, "b": 3})
        await writer.write_file_complete(None)  # type: ignore[arg-type]
        rows = self._read_data_rows(ffill=False)
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
        rows = self._read_data_rows()
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
        rows = self._read_data_rows()
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
        rows = self._read_data_rows(ffill=True)
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

        rows = self._read_data_rows(ffill=True)
        self.assertEqual(rows[0], {"chain_id": "1", "city": "8300"})
        self.assertEqual(rows[1], {"chain_id": "2", "city": "8300"})
        self.assertEqual(
            rows[2], {"chain_id": "3", "city": CSVOutputWriter.EMPTY_STRING}
        )


if __name__ == "__main__":
    unittest.main()
