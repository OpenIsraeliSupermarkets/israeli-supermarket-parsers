import os
import csv
import asyncio
from typing import List
import pandas as pd
from .base_output_writer import BaseOutputWriter
from ..logger import Logger
from ..loading_utils import DumpFile


class CSVOutputWriter(BaseOutputWriter):
    """CSV file output writer with column alignment"""

    EMPTY_STRING = "''"

    def __init__(
        self,
        output_folder: str,
        enabled_scraper: str,
        enabled_file_type: str,
        reduce_duplicates: bool = True,
    ):
        """
        Initialize CSV output writer

        Args:
            output_path: Path to the CSV file
        """
        self._existing_columns: List[str] = []
        self._missing_columns: List[str] = []
        self._header_written = False
        self._initialized = False
        self._reduce_duplicates = reduce_duplicates
        self._previous_row: dict = {}
        self.output_path = os.path.join(
            output_folder,
            enabled_file_type.lower() + "_" + enabled_scraper.lower() + ".csv",
        )

    async def initialize_new_file(self, file: DumpFile) -> None:
        """Initialize the output writer for a new file"""
        self._previous_row = {}

    async def initialize(self) -> None:
        """Initialize the output writer"""
        if not self._initialized:
            # Load existing columns if file exists
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

    async def _append_columns_to_csv(self, new_columns: List[str]) -> None:
        """Append new columns to an existing CSV file"""

        def _do_append():
            output_file = self.output_path.replace(".csv", "_temp.csv")
            with open(self.output_path, "r", encoding="utf-8") as infile, open(
                output_file, "w+", newline="", encoding="utf-8"
            ) as outfile:
                reader = csv.reader(infile)
                writer = csv.writer(outfile)

                # Add header
                header = next(reader)
                writer.writerow(header + new_columns)

                # Add data row-by-row
                for row in reader:
                    writer.writerow(row + [self.EMPTY_STRING] * len(new_columns))
            os.remove(self.output_path)
            os.rename(output_file, self.output_path)

        await asyncio.to_thread(_do_append)

    async def _update_columns_for_row(self, row_columns: List[str]) -> None:
        """Set or extend CSV schema to include columns from this row."""
        if not self._header_written:
            self._existing_columns = row_columns
            Logger.debug(
                f"Creating new file {self.output_path} with columns {self._existing_columns}"
            )
        else:
            self._missing_columns = set(row_columns) - set(self._existing_columns)
            if self._missing_columns:
                Logger.debug(
                    f"Appending missing columns {self._missing_columns} to {self.output_path}"
                )
                await self._append_columns_to_csv(list(self._missing_columns))
                self._existing_columns = await asyncio.to_thread(
                    self.get_existing_columns
                )
                if self._previous_row:
                    for col in self._missing_columns:
                        self._previous_row[col] = self.EMPTY_STRING

    async def write_row(self, row: dict) -> None:
        """
        Write a single row to CSV with column alignment

        Args:
            row: Dictionary representing a single row
        """
        if not self._initialized:
            await self.initialize()

        row_columns = list(row.keys())
        await self._update_columns_for_row(row_columns)

        # Align row to match existing schema (add None for missing columns)
        aligned_row = {}
        for col in self._existing_columns:
            aligned_row[col] = row.get(col, self.EMPTY_STRING)

        if self._reduce_duplicates:
            for col in self._existing_columns:
                val = aligned_row[col]
                if (
                    val is not None
                    and val != self.EMPTY_STRING
                    and val == self._previous_row.get(col)
                ):
                    aligned_row[col] = None

            self._previous_row = {
                col: row.get(col, None) for col in self._existing_columns
            }

        # Write row to CSV
        def _write_row():
            file_exists = os.path.exists(self.output_path)
            mode = "a" if file_exists else "w"
            with open(self.output_path, mode, newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._existing_columns)
                if not self._header_written:
                    writer.writeheader()
                    self._header_written = True
                writer.writerow(aligned_row)

        await asyncio.to_thread(_write_row)

    def close(self) -> None:
        """Close the CSV file"""
        return
