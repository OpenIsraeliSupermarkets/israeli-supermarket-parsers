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

        execution_errors = 0
        files_to_process: List[str] = []
        file_count = 0
        store_names_set = set()
        file_types_set = set()

        Logger.info("Starting streaming file processing")

        self.parser_status.on_parsing_start(
            limit=limit,
            files_types=files_types,
            store_name=",".join(store_names) if store_names else None,
        )

        async for file in self.data_loader.load(limit=limit, store_names=store_names, files_types=files_types):
            file_count += 1
            files_to_process.append(file.file_name)
            store_names_set.add(file.extracted_chain_id)
            file_types_set.add(
                file.detected_filetype.name
                if hasattr(file.detected_filetype, "name")
                else str(file.detected_filetype)
            )

            Logger.debug(f"Processing file {file.file_name}")

            if not file.is_expected_to_be_readable:
                self.parser_status.register_skipped_file(file)
                Logger.debug(f"File {file.file_name} is empty, skipping")
                continue

            row_count = 0
            try:
                parser: BaseFileConverter = parser_class()

                async for row in parser.read(file):
                    await self.output_writer.write_row(row)
                    row_count += 1

                self.parser_status.register_processed_file(file, row_count)
                Logger.debug(f"Successfully processed file {file.file_name} with {row_count} rows")

            except Exception as error:  # pylint: disable=broad-exception-caught
                Logger.error(f"Error processing file {file.file_name}: {error}")
                execution_errors += 1
                self.parser_status.register_failed_file(
                    file, row_count, error, traceback.format_exc()
                )

        store_name = ",".join(sorted(store_names_set)) if store_names_set else "unknown"
        files_types_str = ",".join(sorted(file_types_set)) if file_types_set else "unknown"

        Logger.info(f"Finished processing {file_count} files")

        self.parser_status.on_parsing_completed(
            store_name=store_name,
            had_errors=execution_errors > 0,
            output_path=self.output_writer.get_path(),
            total_files=file_count,
        )

        return ExecutionLog(
            status=True,
            store_name=store_name,
            files_types=files_types_str,
            when_date=datetime.now().isoformat(),
            processed_files=file_count > 0,
            execution_errors=execution_errors > 0,
            output_exists=self.output_writer.exists(),
            output_path=self.output_writer.get_path(),
            files_to_process=files_to_process,
            execution_log=self.parser_status.get_file_logs(),
        )
