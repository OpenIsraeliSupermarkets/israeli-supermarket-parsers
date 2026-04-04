import traceback
from datetime import datetime
from typing import List, Optional

from .parser_factory import ParserFactory
from .utils import Logger
from .utils.base_data_loader import BaseDataLoader
from .utils.base_output_writer import BaseOutputWriter
from .utils.parser_status import ParserStatus, create_parser_status
from .utils.types import ExecutionLog
from .engines.base import BaseFileConverter


class RawParsingPipeline:
    """
    processing files with streaming async generators
    """

    def __init__(
        self,
        data_loader: BaseDataLoader,
        output_writer: BaseOutputWriter,
        parser_status: Optional[ParserStatus] = None,
    ) -> None:
        """
        Initialize RawParsingPipeline

        Args:
            data_loader: DataLoader instance to load files
            output_writer: OutputWriter instance to write results
            parser_status: Tracks and persists per-file outcomes. Defaults to a
                           JsonDataBase-backed ParserStatus writing to "outputs/".
        """
        self.data_loader = data_loader
        self.output_writer = output_writer
        self.parser_status = parser_status or create_parser_status("default")

    async def process(
        self,
        limit: Optional[int] = None,
        store_names: Optional[List[str]] = None,
        files_types: Optional[List[str]] = None,
    ) -> ExecutionLog:
        """start processing the files selected in the pipeline input with streaming"""
        parser_class: BaseFileConverter = ParserFactory.get(store_names)
    
        await self.output_writer.initialize()

        Logger.info("Starting streaming file processing")
        
        files_to_process: List[str] = []
        self.parser_status.on_parsing_start(
            limit=limit,
            files_types=files_types,
            store_name=store_names
        )

        async for file in self.data_loader.load(limit=limit, store_names=store_names, files_types=files_types):
            Logger.debug(f"Processing file {file.file_name}")

            if not file.is_expected_to_be_readable:
                self.parser_status.register_skipped_file(file)
                Logger.debug(f"File {file.file_name} is empty, skipping")
                continue

            row_count = 0
            write_error_count = 0
            try:
                parser: BaseFileConverter = parser_class()

                async for row in parser.read(file):
                    try:
                        await self.output_writer.write_row(row)
                    except Exception as error:  # pylint: disable=broad-exception-caught
                        Logger.error(f"Error writing row {row} to output: {error}")
                        write_error_count += 1
                    row_count += 1

                self.parser_status.register_processed_file(file, row_count, write_error_count)
                Logger.debug(f"Successfully processed file {file.file_name} with {row_count} rows")

            except Exception as error:  # pylint: disable=broad-exception-caught
                Logger.error(f"Error processing file {file.file_name}: {error}")
                execution_errors += 1
                self.parser_status.register_failed_file(
                    file, row_count, error, traceback.format_exc()
                )

        self.parser_status.on_parsing_completed(
            store_names=store_names,
            had_errors=execution_errors > 0,
            output_path=self.output_writer.get_path(),
            files_types=files_types,
            files_to_process=files_to_process,
        )
