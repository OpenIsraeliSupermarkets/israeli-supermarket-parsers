import traceback
import xml.etree.ElementTree as ET
from typing import List, Optional


from .parser_factory import ParserFactory
from .utils import Logger
from .utils.data_loaders import BaseDataLoader
from .utils.output_writers import BaseOutputWriter
from .utils.status import ParserStatus
from .utils.types import ExecutionLog, FileCompleteMessage
from .engines.base import BaseFileConverter


class RawParsingPipeline:
    """
    processing files with streaming async generators
    """

    def __init__(
        self,
        data_loader: BaseDataLoader,
        output_writer: BaseOutputWriter,
        parser_status: ParserStatus,
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
        self.parser_status = parser_status

    async def process(
        self,
        enabled_scraper: str,
        enabled_file_types: str,
        limit: Optional[int] = None,
    ) -> ExecutionLog:
        """start processing the files selected in the pipeline input with streaming"""
        parser_class: BaseFileConverter = ParserFactory.get(enabled_scraper)

        await self.output_writer.initialize()

        Logger.info("Starting streaming file processing")

        files_to_process: List[str] = []
        execution_errors = 0
        self.parser_status.on_parsing_start(
            limit=limit,
            enabled_file_types=enabled_file_types,
            enabled_scraper=enabled_scraper,
        )

        async for file in self.data_loader.load(
            limit=limit,
            enabled_scraper=[enabled_scraper],
            files_types=enabled_file_types,
        ):
            Logger.debug(f"Processing file {file.file_name}")

            if not file.is_expected_to_be_readable:
                self.parser_status.register_skipped_file(file)
                Logger.debug(f"File {file.file_name} is empty, skipping")
                continue

            self.parser_status.registered_file_to_process(file)

            row_count = 0
            write_error_count = 0
            try:
                parser: BaseFileConverter = parser_class()

                await self.output_writer.initialize_new_file(file)

                async for row in parser.read(file):
                    try:
                        await self.output_writer.write_row(row)
                    except (
                        OSError,
                        TypeError,
                        ValueError,
                        RuntimeError,
                        KeyError,
                    ) as error:
                        Logger.error(f"Error writing row {row} to output: {error}")
                        write_error_count += 1
                    row_count += 1

                self.parser_status.register_processed_file(file, row_count)
                await self.output_writer.write_file_complete(
                    FileCompleteMessage(
                        file_name=file.file_name,
                        total_expected_records=row_count,
                    )
                )
                Logger.debug(
                    f"Successfully processed file {file.file_name} with {row_count} rows"
                )

            except (
                OSError,
                TypeError,
                ValueError,
                RuntimeError,
                KeyError,
                ET.ParseError,
            ) as error:
                Logger.error(f"Error processing file {file.file_name}: {error}")
                execution_errors += 1
                self.parser_status.register_failed_file(
                    file, row_count, error, traceback.format_exc()
                )

        self.parser_status.on_parsing_completed(
            enabled_scraper=enabled_scraper,
            enabled_file_types=enabled_file_types,
            had_errors=execution_errors > 0,
            output_path=self.output_writer.get_path(),
            total_files=len(files_to_process),
        )

    def get_parser_status(self) -> ParserStatus:
        """Return the status tracker used by this pipeline."""
        return self.parser_status
