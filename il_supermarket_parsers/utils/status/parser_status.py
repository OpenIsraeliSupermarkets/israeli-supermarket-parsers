"""Parser execution status tracker.

Mirrors the ScraperStatus pattern from il_supermarket_scarper:
  - ParserStatus        ↔  ScraperStatus
  - create_parser_status ↔  create_status_database_for_scraper

Reuses the JsonDataBase / MongoDataBase backends from the scraper package
so that both systems write structured, collection-based JSON files with
the same on-disk format.
"""

import os
from datetime import datetime
from typing import List, Optional

from il_supermarket_scarper.utils.databases.base import AbstractDataBase

from ..loading_utils import DumpFile
from ..logger import Logger
from ..types import FileExecutionLog
from .parser_status_contract import (
    CompletedParsingStatus,
    FailedFileStatus,
    ProcessedFileStatus,
    SkippedFileStatus,
    StartedParsingStatus,
)


def _now() -> datetime:
    return datetime.now()


class ParserStatus:
    """Abstracts the database interface for parser execution status.

    Analogous to ScraperStatus in il_supermarket_scarper.

    Each parsing run (one store × one file-type combination) should use
    its own ParserStatus instance backed by a dedicated database.

    Event lifecycle:
        on_parsing_start()
        → register_skipped_file()   (0..n times)
        → register_processed_file() (0..n times)
        → register_failed_file()    (0..n times)
        on_parsing_completed()
    """

    STARTED = "started"
    PROCESSED = "processed"
    SKIPPED = "skipped"
    FAILED = "failed"
    COMPLETED = "completed"

    def __init__(self, database_name: str, status_database: AbstractDataBase) -> None:
        self.database_name = database_name
        self.database = status_database
        self._file_logs: List[FileExecutionLog] = []

    def _dumpfile_to_event_fields(self, dump_file: DumpFile) -> dict:
        """Minimal fields shared by all per-file contract events."""
        return {
            "file_name": dump_file.file_name,
            "store_folder": dump_file.store_folder,
            "file_type": (
                dump_file.detected_filetype.name
                if hasattr(dump_file.detected_filetype, "name")
                else str(dump_file.detected_filetype)
            ),
        }

    def _dumpfile_to_execution_log_fields(self, dump_file: DumpFile) -> dict:
        """Fields needed to build a FileExecutionLog (in-memory return value)."""
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
            "extracted_date": (
                dump_file.extracted_date.isoformat()
                if isinstance(dump_file.extracted_date, datetime)
                else str(dump_file.extracted_date)
            ),
            "detected_filetype": (
                dump_file.detected_filetype.name
                if hasattr(dump_file.detected_filetype, "name")
                else str(dump_file.detected_filetype)
            ),
            "size": str(file_size),
            "is_expected_to_have_records": dump_file.is_expected_to_have_records,
        }

    def on_parsing_start(
        self,
        limit: Optional[int],
        enabled_file_types: Optional[List[str]],
        enabled_scraper: Optional[str],
    ) -> None:
        """Record that a parsing run has started."""
        event = StartedParsingStatus(
            when=_now(),
            limit=limit,
            scraper=enabled_scraper,
            files_types=enabled_file_types,
        )
        self.database.insert_document("global_status", event.dict())

    def register_skipped_file(self, dump_file: DumpFile) -> None:
        """Record that a file was skipped because it is not readable."""
        event = SkippedFileStatus(
            when=_now(), **self._dumpfile_to_event_fields(dump_file)
        )
        self.database.insert_document("events", event.dict())

        fields = self._dumpfile_to_execution_log_fields(dump_file)
        fields.update({"loaded": False, "succusfull": None})
        self._file_logs.append(FileExecutionLog(**fields))

    def register_processed_file(self, dump_file: DumpFile, row_count: int) -> None:
        """Record that a file was parsed successfully."""
        event = ProcessedFileStatus(
            when=_now(),
            row_count=row_count,
            **self._dumpfile_to_event_fields(dump_file),
        )
        self.database.insert_document("events", event.dict())

        fields = self._dumpfile_to_execution_log_fields(dump_file)
        fields.update(
            {"loaded": True, "succusfull": True, "detected_num_rows": row_count}
        )
        self._file_logs.append(FileExecutionLog(**fields))

    def register_failed_file(
        self,
        dump_file: DumpFile,
        row_count: int,
        error: Exception,
        trace: str,
    ) -> None:
        """Record that a file failed during processing."""
        event = FailedFileStatus(
            when=_now(),
            row_count=row_count,
            error=str(error),
            trace=trace,
            **self._dumpfile_to_event_fields(dump_file),
        )
        self.database.insert_document("events", event.dict())

        fields = self._dumpfile_to_execution_log_fields(dump_file)
        fields.update(
            {
                "loaded": True,
                "succusfull": False,
                "detected_num_rows": row_count,
                "error": str(error),
                "trace": trace,
            }
        )
        self._file_logs.append(FileExecutionLog(**fields))

    def on_parsing_completed(
        self,
        enabled_scraper: str,
        enabled_file_types: List[str],
        had_errors: bool,
        output_path: Optional[str],
        total_files: int,
    ) -> None:
        """Record that the parsing run has finished."""
        event = CompletedParsingStatus(
            when=_now(),
            store_name=enabled_scraper,
            files_types=enabled_file_types,
            had_errors=had_errors,
            output_path=output_path,
            total_files=total_files,
        )
        self.database.insert_document("global_status", event.dict())
        Logger.info(
            "Parser status saved: store=%s, enabled_file_types=%s "
            "files=%s, errors=%s",
            enabled_scraper,
            enabled_file_types,
            total_files,
            had_errors,
        )

    def get_file_logs(self) -> List[FileExecutionLog]:
        """Return in-memory file logs for building an ExecutionLog return value."""
        return list(self._file_logs)
