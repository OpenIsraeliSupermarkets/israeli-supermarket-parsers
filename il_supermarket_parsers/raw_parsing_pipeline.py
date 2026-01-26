import traceback
import os
from typing import Any, List, Optional
from datetime import datetime

from .parser_factory import ParserFactory
from .utils import DumpFile, Logger
from .utils.base_data_loader import BaseDataLoader
from .utils.base_output_writer import BaseOutputWriter
from .utils.types import ExecutionLog, FileExecutionLog
from .engines.base import BaseFileConverter


def _dumpfile_to_file_execution_log(dump_file: DumpFile) -> dict:
    """Convert DumpFile to FileExecutionLog fields"""
    file_size = 0
    if dump_file.is_queue_based:
        file_size = len(dump_file.file_content) if dump_file.file_content else 0
    else:
        file_path = dump_file.get_full_path
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)

    return {
        "store_folder": dump_file.store_folder,
        "file_name": dump_file.file_name,
        "prefix_file_name": dump_file.prefix_file_name,
        "extracted_store_number": dump_file.extracted_store_number,
        "extracted_chain_id": dump_file.extracted_chain_id,
        "extracted_date": dump_file.extracted_date.isoformat() if isinstance(dump_file.extracted_date, datetime) else str(dump_file.extracted_date),
        "detected_filetype": dump_file.detected_filetype.name if hasattr(dump_file.detected_filetype, 'name') else str(dump_file.detected_filetype),
        "size": str(file_size),
        "is_expected_to_have_records": dump_file.is_expected_to_have_records,
    }


class RawParsingPipeline:
    """
    processing files with streaming async generators
    """

    def __init__(
        self,
        data_loader: BaseDataLoader,
        output_writer: BaseOutputWriter,
    ) -> None:
        """
        Initialize RawParsingPipeline

        Args:
            data_loader: DataLoader instance to load files
            output_writer: OutputWriter instance to write results
        """
        self.data_loader = data_loader
        self.output_writer = output_writer

    async def process(
        self, 
        limit: Optional[int] = None, 
        store_names: Optional[List[str]] = None, 
        files_types: Optional[List[str]] = None
    ) -> ExecutionLog:
        """start processing the files selected in the pipeline input with streaming"""
        parser_class: BaseFileConverter = ParserFactory.get(store_names)

        # Initialize output writer
        await self.output_writer.initialize()

        execution_log: List[FileExecutionLog] = []
        execution_errors = 0
        files_to_process: List[str] = []
        file_count = 0
        store_names_set = set()
        file_types_set = set()

        Logger.info("Starting streaming file processing")

        async for file in self.data_loader.load(limit=limit, store_names=store_names, files_types=files_types):
            file_count += 1
            files_to_process.append(file.file_name)
            store_names_set.add(file.extracted_chain_id)
            file_types_set.add(file.detected_filetype.name if hasattr(file.detected_filetype, 'name') else str(file.detected_filetype))

            Logger.debug(f"Processing file {file.file_name}")
            
            # ignore but log empty files
            if not file.is_expected_to_be_readable:
                log_data = _dumpfile_to_file_execution_log(file)
                log_data.update({
                    "loaded": False,
                    "succusfull": None,
                })
                execution_log.append(FileExecutionLog(**log_data))
                Logger.debug(f"File {file.file_name} is empty, skipping")
                continue

            # if the file is not empty, process it
            row_count = 0
            try:
                parser: BaseFileConverter = parser_class()
                
                # Process rows one by one
                async for row in parser.read(file):
                    await self.output_writer.write_row(row)
                    row_count += 1

                log_data = _dumpfile_to_file_execution_log(file)
                log_data.update({
                    "loaded": True,
                    "succusfull": True,
                    "detected_num_rows": row_count,
                })
                execution_log.append(FileExecutionLog(**log_data))
                Logger.debug(f"Successfully processed file {file.file_name} with {row_count} rows")

            except Exception as error:  # pylint: disable=broad-exception-caught
                Logger.error(f"Error processing file {file.file_name}: {error}")
                execution_errors += 1
                log_data = _dumpfile_to_file_execution_log(file)
                log_data.update({
                    "loaded": True,
                    "succusfull": False,
                    "detected_num_rows": row_count,
                    "error": str(error),
                    "trace": traceback.format_exc(),
                })
                execution_log.append(FileExecutionLog(**log_data))

        # Determine store_name and files_types from processed files
        store_name = ",".join(sorted(store_names_set)) if store_names_set else "unknown"
        files_types_str = ",".join(sorted(file_types_set)) if file_types_set else "unknown"

        Logger.info(f"Finished processing {file_count} files")

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
            execution_log=execution_log,
        )
