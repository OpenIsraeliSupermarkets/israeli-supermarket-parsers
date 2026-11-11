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
    verify_extraction: bool = False,
) -> Tuple[Optional[pd.DataFrame], bool, int]:
    """Parse one dump file through CSVOutputWriter and read it back.

    Mirrors the validation pipeline in ``test_case._process_files``:
    ``parser.read`` → ``CSVOutputWriter`` → ``read_data_rows``.

    With ``verify_extraction`` the yielded rows are also checked by the
    production verifier (:meth:`BaseFileConverter.verify_extraction`), so the
    chain tests run it on live files next to ``run_validation``.

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

        rows = [] if verify_extraction else None
        async for row in parser.read(file, run_validation=verify_extraction):
            row_count += 1
            await writer.write_row(row)
            if rows is not None:
                rows.append(row)

        await writer.close()
        if rows is not None:
            parser.verify_extraction(file, rows)
            del rows

        csv_created = writer.exists()
        if not csv_created:
            return None, False, row_count

        df = read_data_rows(
            writer.get_path(), ffill=reduce_duplicates, as_records=False
        )
        return df, True, row_count
