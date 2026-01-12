import os
import csv
from typing import List
import pandas as pd
from .base_output_writer import BaseOutputWriter
from .logger import Logger


class CSVOutputWriter(BaseOutputWriter):
    """CSV file output writer with column alignment"""

    def __init__(self, output_path: str):
        """
        Initialize CSV output writer

        Args:
            output_path: Path to the CSV file
        """
        self.output_path = output_path

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
        except Exception:
            return []

    def append_columns_to_csv(self, new_columns: List[str]) -> None:
        """Append new columns to an existing CSV file"""
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
                writer.writerow(row + [""] * len(new_columns))
        os.remove(self.output_path)
        os.rename(output_file, self.output_path)

    def write_batch(self, df: pd.DataFrame) -> None:
        """
        Write a DataFrame batch to CSV with column alignment

        Args:
            df: DataFrame to write
        """
        if not self.exists():
            Logger.debug(f"Creating new file {self.output_path}")
            df.to_csv(self.output_path, index=False, mode="w", header=True)
        else:
            Logger.debug(f"File exists, processing batch")
            existing_columns = self.get_existing_columns()

            # If there are missing columns in the existing file, append them
            missing_columns = set(df.columns) - set(existing_columns)
            if missing_columns:
                Logger.debug(
                    f"Appending missing columns {missing_columns} to {self.output_path}"
                )
                self.append_columns_to_csv(list(missing_columns))
                existing_columns = self.get_existing_columns()

            # If there are missing columns in the new DataFrame, add them
            all_columns = list(set(existing_columns) - set(df.columns))
            for column in all_columns:
                if column not in df.columns:
                    df[column] = None  # Add missing columns with None values

            # Write aligned DataFrame
            df[existing_columns].to_csv(
                self.output_path, index=False, mode="a", header=False
            )
            Logger.debug(f"Appending data to {self.output_path}")
