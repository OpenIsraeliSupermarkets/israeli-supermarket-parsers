"""Shared parse → CSV → read-back path for validation."""

from __future__ import annotations

import tempfile
from typing import Optional, Tuple

import pandas as pd

from il_supermarket_parsers.engines.base import BaseFileConverter
from il_supermarket_parsers.utils.csv_reader import read_data_rows
from il_supermarket_parsers.utils.loading_utils import DumpFile
from il_supermarket_parsers.utils.output_writers.csv_output_writer import (
    CSVOutputWriter,
)


async def parse_file_via_csv(
    parser: BaseFileConverter,
    file: DumpFile,
    *,
    reduce_duplicates: bool = True,
) -> Tuple[Optional[pd.DataFrame], bool, int]:
    """Parse one dump file through CSVOutputWriter and read it back.

    Mirrors the validation pipeline in ``test_case._process_files``:
    ``parser.read`` → ``CSVOutputWriter`` → ``read_data_rows``.

    Returns:
        ``(dataframe or None, csv_was_created, parsed_row_count)``
    """
    row_count = 0
    with tempfile.TemporaryDirectory() as file_tmp_dir:
        writer = CSVOutputWriter(
            output_folder=file_tmp_dir,
            csv_file_name=(
                f"{file.detected_filetype.name.lower()}_"
                f"{file.extracted_chain_id.lower()}"
            ),
            reduce_duplicates=reduce_duplicates,
        )
        await writer.initialize()

        async for row in parser.read(file):
            row_count += 1
            await writer.write_row(row)

        await writer.close()

        csv_created = writer.exists()
        if not csv_created:
            return None, False, row_count

        df = read_data_rows(
            writer.get_path(), ffill=reduce_duplicates, as_records=False
        )
        return df, True, row_count
