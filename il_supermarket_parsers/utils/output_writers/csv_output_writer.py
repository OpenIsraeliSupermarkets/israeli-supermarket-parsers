import os
import json
import asyncio
import csv
from typing import Any, List

import pandas as pd
import numpy as np
from .base_output_writer import BaseOutputWriter
from ..logger import Logger
from ..loading_utils import DumpFile
from ..types import FileCompleteMessage


class CSVOutputWriter(BaseOutputWriter):
    """
    CSV file output writer with column alignment and deduplication.
    
    If reduce_duplicates is True, repeated values are masked with CELL_TO_BE_SMOTED such that ffill() can restore the value.
    If reduce_duplicates is False, repeated values are preserved.
    
    The EMPTY_STRING is used to indicate a missing value in the original CSV.
    
    """

    EMPTY_STRING = "''"
    CELL_TO_BE_SMOTED = np.nan

    def __init__(
        self,
        output_folder: str,
        enabled_scraper: str,
        enabled_file_type: str,
        reduce_duplicates: bool = True,
    ):
        self._initialized = False
        self._header_written = False
        self._existing_columns: List[str] = []
        self._reduce_duplicates = reduce_duplicates
        self._buffer: list[dict] = []
        self.output_path = os.path.join(
            output_folder,
            enabled_file_type.lower() + "_" + enabled_scraper.lower() + ".csv",
        )

    def _serialize_cell_for_csv(self, value: Any) -> Any:
        """
        Write nested structures as JSON so tests and downstream code can
        :func:`json.loads` cells after :func:`pandas.read_csv` and recover all keys
        (required by XML key validation for promo feeds with nested items/groups).
        """
        if isinstance(value, (dict, list)):
            return json.dumps(value, default=str, ensure_ascii=False)
        return value

    async def initialize_new_file(self, file: DumpFile) -> None:
        """Reset per-file row buffer."""
        self._buffer = []

    async def initialize(self) -> None:
        """Initialize the output writer"""
        if not self._initialized:
            if self.exists():
                self._existing_columns = await asyncio.to_thread(
                    self.get_existing_columns
                )
                self._header_written = True
                Logger.debug(
                    f"Initialized CSV writer, found existing columns: {self._existing_columns}"
                )
            else:
                Logger.debug(f"Initializing new CSV file {self.output_path}")
            self._initialized = True

    def exists(self) -> bool:
        """Check if CSV file exists"""
        return os.path.exists(self.output_path)

    def get_path(self) -> str:
        """Get the CSV file path"""
        return self.output_path

    def get_existing_columns(self) -> List[str]:
        """Get existing columns from CSV file"""
        if not self.exists():
            return []
        try:
            existing_df = pd.read_csv(self.output_path, nrows=0)
            return list(existing_df.columns)
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError):
            return []

    async def write_row(self, row: dict) -> None:
        """Buffer a single row; flushed to disk on write_file_complete."""
        if not self._initialized:
            await self.initialize()
        self._buffer.append(row)

    async def write_file_complete(self, _message: "FileCompleteMessage") -> None:
        """Flush the buffered rows for one file to disk as a single DataFrame write."""
        if not self._buffer:
            return

        await asyncio.to_thread(self._flush_buffer)
        self._buffer = []

    def _flush_buffer(self) -> None:
        """Build, align, deduplicate, and append the buffered rows to the CSV."""
        # Preserve insertion-order column discovery across all rows in this file.
        all_cols = list(dict.fromkeys(k for row in self._buffer for k in row))

        # Fill missing keys with the schema-evolution sentinel (not NaN) so that
        # the sentinel is distinguishable from dedup-masked cells (NaN) downstream.
        # Also normalise genuinely-empty source values to the sentinel so that
        # callers can distinguish "column absent" from "dedup-masked" (NaN).
        def _norm(v: Any) -> Any:
            if v is None:
                return None
            if v == "":
                return self.EMPTY_STRING
            if isinstance(v, (dict, list)):
                return json.dumps(v, default=str, ensure_ascii=False)
            # Convert to string early so dedup masking never promotes int → float.
            return str(v)

        normalized = [
            {col: _norm(row.get(col, self.EMPTY_STRING)) for col in all_cols}
            for row in self._buffer
        ]
        df = pd.DataFrame(normalized, columns=all_cols, dtype=str)

        if self._reduce_duplicates:
            # Mask repeated values but never mask the schema-evolution sentinel.
            sentinel_mask = df == self.EMPTY_STRING
            repeat_mask = df == df.shift()
            df = df.mask(repeat_mask & ~sentinel_mask)

        # Align with the schema already written to the output file.
        if not self._header_written:
            self._existing_columns = list(df.columns)
        else:
            # New columns in this file → add them (with sentinel) to the existing CSV.
            new_cols = [c for c in df.columns if c not in self._existing_columns]
            if new_cols:
                Logger.debug(
                    f"Appending missing columns {new_cols} to {self.output_path}"
                )
                self._append_columns_to_csv_sync(new_cols)
                self._existing_columns = self.get_existing_columns()

            # Columns in existing CSV missing from this file → fill with sentinel.
            for col in self._existing_columns:
                if col not in df.columns:
                    df[col] = self.EMPTY_STRING

        # Write in existing column order.
        df = df[self._existing_columns]

        file_exists = os.path.exists(self.output_path)
        mode = "a" if file_exists else "w"
        df.to_csv(
            self.output_path,
            index=False,
            mode=mode,
            header=not self._header_written,
            encoding="utf-8",
        )
        if not self._header_written:
            self._header_written = True

    def _append_columns_to_csv_sync(self, new_columns: List[str]) -> None:
        """Add new columns (filled with sentinel) to an existing CSV file."""
        output_file = self.output_path.replace(".csv", "_temp.csv")
        with open(self.output_path, "r", encoding="utf-8") as infile, open(
            output_file, "w+", newline="", encoding="utf-8"
        ) as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            header = next(reader)
            writer.writerow(header + new_columns)
            for row in reader:
                writer.writerow(row + [self.EMPTY_STRING] * len(new_columns))
        os.remove(self.output_path)
        os.rename(output_file, self.output_path)

    def close(self) -> None:
        """Close the CSV file"""
        return
