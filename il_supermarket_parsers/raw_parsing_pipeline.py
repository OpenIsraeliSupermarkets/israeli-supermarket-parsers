import traceback
from dataclasses import dataclass, field
from typing import Any, List, Optional

from tqdm import tqdm
from .parser_factory import ParserFactory
from .utils import DumpFile, Logger
from .utils.base_data_loader import BaseDataLoader
from .utils.base_output_writer import BaseOutputWriter
from .utils.types import ExecutionLog, FileExecutionLog
from .engines.base import BaseFileConverter
import pandas as pd

class RawParsingPipeline:
    """
    processing files to dataframe
    """

    def __init__(
        self,
        store_name: str,
        file_type: str,
        when_date,
        data_loader: BaseDataLoader,
        output_writer: BaseOutputWriter,
    ) -> None:
        """
        Initialize RawParsingPipeline

        Args:
            store_name: Name of the store
            file_type: Type of file to process
            when_date: Date when processing
            data_loader: DataLoader instance to load files
            output_writer: OutputWriter instance to write results
        """
        self.store_name = store_name
        self.file_type = file_type
        self.when_date = when_date
        self.data_loader = data_loader
        self.output_writer = output_writer

    def process(self, limit=None) -> ExecutionLog:
        """start processing the files selected in the pipeline input"""
        parser_class: BaseFileConverter = ParserFactory.get(self.store_name)

        files_to_process: List[DumpFile] = self.data_loader.load(limit=limit, store_names=[self.store_name], files_types=[self.file_type])

        Logger.info(
            f"Processing {len(files_to_process)} files"
            f"of type {self.file_type} for store {self.store_name}"
        )
        execution_log: List[FileExecutionLog] = []
        execution_errors = 0
        for file in tqdm(
            files_to_process,
            total=len(files_to_process),
            desc=f"Processing {self.file_type}@{self.store_name}",
        ):

            Logger.debug(f"Processing file {file.file_name}")
            # ignore but log empty files
            if file.is_expected_to_be_readable():
                execution_log.append(
                    FileExecutionLog(
                        loaded=False,
                        file=file
                    )
                )
                Logger.debug(f"File {file.file_name} is empty, skipping")
                continue

            # if the file is not empty, process it
            try:
                parser: BaseFileConverter = parser_class()
                df: pd.DataFrame = parser.read(file)

                # Write batch using output writer (handles column alignment)
                self.output_writer.write_batch(df)

                execution_log.append(
                    FileExecutionLog(
                        loaded=True,
                        succusfull=True,
                        detected_num_rows=df.shape[0],
                        file=file
                    )
                )

                del df

            except Exception as error:  # pylint: disable=broad-exception-caught
                Logger.error(f"Error processing file {file.file_name}: {error}")
                execution_errors += 1
                execution_log.append(
                    FileExecutionLog(
                        loaded=True,
                        succusfull=False,
                        error=str(error),
                        trace=traceback.format_exc(),
                        file=file
                    )
                )

        return ExecutionLog(
            status=True,
            store_name=self.store_name,
            files_types=self.file_type,
            when_date=self.when_date,
            processed_files=len(files_to_process) > 0,
            execution_errors=execution_errors > 0,
            output_exists=self.output_writer.exists(),
            output_path=self.output_writer.get_path(),
            files_to_process=[dumpfile.file_name for dumpfile in files_to_process],
            execution_log=execution_log,
        )
