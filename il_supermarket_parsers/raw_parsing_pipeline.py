import traceback
import xml.etree.ElementTree as ET
from typing import List, Optional


from .parser_factory import ParserFactory
from .utils import Logger
from .utils.data_loaders import BaseDataLoader
from .utils.data_loaders.queue_router import QueueManagerConnectionError
from .utils.loading_utils import DumpFile
from .utils.output_writers import BaseOutputWriter
from .utils.status import ParserStatus
from .utils.types import ExecutionLog, FileCompleteMessage
from .engines.base import BaseFileConverter


class RawParsingPipeline:
    """
    processing files with streaming async generators

    ``process`` runs a whole (scraper, file type) job from the data loader.
    Queue workers call ``start`` / ``process_file`` / ``finish`` themselves,
    because they receive files for several jobs interleaved on one inbox.
    """

    def __init__(
        self,
        data_loader: Optional[BaseDataLoader],
        output_writer: BaseOutputWriter,
        parser_status: ParserStatus,
    ) -> None:
        """
        Initialize RawParsingPipeline

        Args:
            data_loader: DataLoader instance to load files. Only ``process``
                         uses it; it may be None when files are fed in.
            output_writer: OutputWriter instance to write results
            parser_status: Tracks and persists per-file outcomes. Defaults to a
                           JsonDataBase-backed ParserStatus writing to "outputs/".
        """
        self.data_loader = data_loader
        self.output_writer = output_writer
        self.parser_status = parser_status
        self._parser_class = None
        self._enabled_scraper: Optional[str] = None
        self._enabled_file_types: Optional[str] = None
        self._files_to_process: List[DumpFile] = []
        self._execution_errors = 0

    async def process(
        self,
        enabled_scraper: str,
        enabled_file_types: str,
        limit: Optional[int] = None,
    ) -> ExecutionLog:
        """start processing the files selected in the pipeline input with streaming"""
        await self.start(enabled_scraper, enabled_file_types, limit=limit)

        manager_error: Optional[BaseException] = None
        try:
            async for file in self.data_loader.load(
                limit=limit,
                enabled_scraper=[enabled_scraper],
                files_types=[enabled_file_types],
            ):
                await self.process_file(file)
        except QueueManagerConnectionError as error:
            manager_error = error

        self.finish(had_errors=manager_error is not None)
        if manager_error is not None:
            raise manager_error

    async def start(
        self,
        enabled_scraper: str,
        enabled_file_types: str,
        limit: Optional[int] = None,
    ) -> None:
        """Open the output and record that this job has started."""
        self._parser_class = ParserFactory.get(enabled_scraper)
        self._enabled_scraper = enabled_scraper
        self._enabled_file_types = enabled_file_types
        self._files_to_process = []
        self._execution_errors = 0

        await self.output_writer.initialize()

        Logger.info("Starting streaming file processing")

        self.parser_status.on_parsing_start(
            limit=limit,
            enabled_file_types=enabled_file_types,
            enabled_scraper=enabled_scraper,
        )

    async def process_file(self, file: DumpFile) -> None:
        """Parse one file, write its rows, and record the outcome."""
        Logger.debug(f"Processing file {file.file_name}")
        self._files_to_process.append(file)

        if not file.is_expected_to_be_readable:
            self.parser_status.register_skipped_file(file)
            Logger.debug(f"File {file.file_name} is empty, skipping")
            return

        self.parser_status.registered_file_to_process(file)

        row_count = 0
        try:
            parser: BaseFileConverter = self._parser_class()

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
            self._execution_errors += 1
            self.parser_status.register_failed_file(
                file, row_count, error, traceback.format_exc()
            )

    def finish(self, had_errors: bool = False) -> None:
        """Record that this job completed.

        Args:
            had_errors: Also mark the job failed for an error outside a file,
                such as a lost queue connection.
        """
        self.parser_status.on_parsing_completed(
            enabled_scraper=self._enabled_scraper,
            enabled_file_types=self._enabled_file_types,
            had_errors=had_errors or self._execution_errors > 0,
            output_path=self.output_writer.get_path(),
            total_files=len(self._files_to_process),
        )

    def get_parser_status(self) -> ParserStatus:
        """Return the status tracker used by this pipeline."""
        return self.parser_status
