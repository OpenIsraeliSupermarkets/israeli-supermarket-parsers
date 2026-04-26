import csv
import os
import tempfile
import unittest

from pandas._libs.lib import infer_dtype
from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)
import pandas as pd


class TestCSVOutputWriter(unittest.IsolatedAsyncioTestCase):
    """Integration tests for CSVOutputWriter (real files, no mocks)."""

    def setUp(self) -> None:
        self._tmpdir = (
            tempfile.TemporaryDirectory()
        )  # pylint: disable=consider-using-with
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
        df = pd.read_csv(self._csv_path(), dtype=str)
        if ffill:
            df = df.ffill()
        return df.to_dict(orient="records")

    async def test_initialize_sets_initialized_flag(self) -> None:
        writer = self._new_writer()
        self.assertFalse(writer._initialized)  # pylint: disable=protected-access
        self.assertFalse(writer._header_written)  # pylint: disable=protected-access
        await writer.initialize()
        self.assertTrue(writer._initialized)  # pylint: disable=protected-access
        self.assertFalse(writer._header_written)  # pylint: disable=protected-access

    async def test_initialize_reads_existing_file_columns(self) -> None:
        with open(self._csv_path(), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["x", "y", "z"])
            w.writerow([1, 2, 3])
        writer = self._new_writer()
        await writer.initialize()
        self.assertEqual(
            writer._existing_columns,
            ["x", "y", "z"],  # pylint: disable=protected-access
        )
        self.assertTrue(writer._header_written)  # pylint: disable=protected-access

    async def test_initialize_is_idempotent(self) -> None:
        writer = self._new_writer()
        await writer.initialize()
        await writer.initialize()
        self.assertTrue(writer._initialized)  # pylint: disable=protected-access

    async def test_write_row_content(self) -> None:
        writer = self._new_writer()
        await writer.write_row({"name": "foo", "value": 42})
        rows = self._read_data_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], {"name": "foo", "value": "42"})

    async def test_write_multiple_rows_same_schema(self) -> None:
        writer = self._new_writer()
        for i in range(3):
            await writer.write_row({"id": i, "k": f"v{i}"})
        rows = self._read_data_rows()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], {"id": "0", "k": "v0"})
        self.assertEqual(rows[1], {"id": "1", "k": "v1"})
        self.assertEqual(rows[2], {"id": "2", "k": "v2"})

    async def test_schema_evolution_adds_new_column(self) -> None:
        writer = self._new_writer()
        await writer.write_row({"a": 1})
        await writer.write_row({"a": 2, "b": 3})
        rows = self._read_data_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "''"})
        self.assertEqual(rows[1], {"a": "2", "b": "3"})

    async def test_schema_evolution_removes_column(self) -> None:
        writer = self._new_writer()
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_row({"a": 1})
        rows = self._read_data_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})

        self.assertTrue(pd.isna(rows[1]["a"]))
        self.assertEqual(rows[1]["b"], "''")

    async def test_reduce_duplicates_nullifies_repeated_value(self) -> None:
        writer = self._new_writer(reduce_duplicates=True)
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_row({"a": 1, "b": 3})
        rows = self._read_data_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})
        # NaN != NaN in Python; assert the repeated value was elided in CSV (empty → NaN)
        self.assertTrue(pd.isna(rows[1]["a"]))
        self.assertEqual(rows[1]["b"], "3")

        rows = self._read_data_rows(ffill=True)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})
        self.assertEqual(rows[1], {"a": "1", "b": "3"})

    async def test_no_reduce_duplicates_preserves_all_values(self) -> None:
        writer = self._new_writer(reduce_duplicates=False)
        await writer.write_row({"a": 1, "b": 2})
        await writer.write_row({"a": 1, "b": 3})
        rows = self._read_data_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"a": "1", "b": "2"})
        self.assertEqual(rows[1], {"a": "1", "b": "3"})

    async def test_no_dedup_across_files(self) -> None:
        writer = self._new_writer(reduce_duplicates=True)
        await writer.initialize_new_file(None)  # type: ignore[arg-type]
        await writer.write_row({"a": 1, "b": 2})
        await writer.initialize_new_file(None)  # type: ignore[arg-type]
        await writer.write_row({"a": 1, "b": 2})
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


if __name__ == "__main__":
    unittest.main()
