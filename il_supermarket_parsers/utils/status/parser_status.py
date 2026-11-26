"""Parser execution status tracker.

Mirrors the ScraperStatus pattern from il_supermarket_scarper:
  - ParserStatus        ↔  ScraperStatus
  - create_parser_status ↔  create_status_database_for_scraper

Reuses the JsonDataBase / MongoDataBase backends from the scraper package
so that both systems write structured, collection-based JSON files with
the same on-disk format.
"""

import hashlib
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set

from il_supermarket_scarper.utils.databases.base import AbstractDataBase

from ..loading_utils import DumpFile
from ..logger import Logger
from ..types import FileExecutionLog
from .parser_status_contract import (
    AlreadyParsedFile,
    CompletedParsingStatus,
    FailedFileStatus,
    ParsedFile,
    ProcessedFileStatus,
    SkippedFileStatus,
    StartedParsingStatus,
    RegisteredFileToProcessStatus,
)


def _now() -> datetime:
    return datetime.now()


def dump_file_sha256(dump_file: DumpFile) -> Optional[str]:
    """SHA-256 of the dump's bytes, or None when the file is not there (#154).

    Queue-based dumps hash their in-memory content; folder dumps are read in
    1 MiB chunks so a large file is never held in memory.
    """
    digest = hashlib.sha256()
    if dump_file.is_queue_based:
        digest.update(dump_file.file_content)
        return digest.hexdigest()
    if not os.path.exists(dump_file.get_full_path):
        return None
    with open(dump_file.get_full_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    PARSED_FILES = "parsed_files"
    ALREADY_PARSED = "already_parsed"

    def __init__(self, status_database: AbstractDataBase) -> None:
        self.database = status_database
        self._file_logs: List[FileExecutionLog] = []
        self.task_id: uuid.UUID = str(uuid.uuid4())
        # file name -> hashes it was parsed with (None: entry from before #154).
        # Read from the database on first use, then kept up to date in memory.
        self._parsed_hashes: Optional[Dict[str, Set[Optional[str]]]] = None

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

    def _record_parsed_file(
        self,
        dump_file: DumpFile,
        row_count: Optional[int],
        content_sha256: Optional[str],
    ) -> None:
        """Append the file to the durable parsed-file registry."""
        row = ParsedFile(
            system_timestamp=_now(),
            row_count=row_count,
            content_sha256=content_sha256,
            task_id=self.task_id,
            **self._dumpfile_to_event_fields(dump_file),
        )
        self.database.insert_document(self.PARSED_FILES, row.dict())
        self._registry().setdefault(dump_file.file_name, set()).add(content_sha256)

    # -- already-parsed check (#154) ---------------------------------------

    def _registry(self) -> Dict[str, Set[Optional[str]]]:
        """The parsed-file registry as file name -> hashes, read once."""
        if self._parsed_hashes is None:
            self._parsed_hashes = {}
            for doc in self.database.list_documents(self.PARSED_FILES):
                if doc.get("file_name"):
                    self._parsed_hashes.setdefault(doc["file_name"], set()).add(
                        doc.get("content_sha256")
                    )
        return self._parsed_hashes

    def was_parsed(self, file_name: str, content_sha256: Optional[str]) -> bool:
        """True when this dump, same name and same content, was parsed before.

        - Name never parsed: False.
        - Name parsed before hashes were recorded: True (we can't tell, and
          parsing it again would duplicate its rows).
        - Otherwise: True only for a hash seen before. The scraper downloads a
          file again under the same name when its content changed, and that
          new content must be parsed.
        - No hash (the file is missing): False, so the normal path handles it.
        """
        hashes = self._registry().get(file_name)
        if not hashes or content_sha256 is None:
            return False
        return None in hashes or content_sha256 in hashes

    def register_already_parsed_file(
        self, dump_file: DumpFile, content_sha256: str
    ) -> None:
        """Record a dump left out because it was parsed before."""
        row = AlreadyParsedFile(
            system_timestamp=_now(),
            content_sha256=content_sha256,
            task_id=self.task_id,
            **self._dumpfile_to_event_fields(dump_file),
        )
        self.database.insert_document(self.ALREADY_PARSED, row.dict())

    def parsed_file_names(self) -> Set[str]:
        """Return every file name recorded in the parsed-file registry."""
        return {
            doc["file_name"]
            for doc in self.database.list_documents(self.PARSED_FILES)
            if doc.get("file_name")
        }

    def on_parsing_start(
        self,
        limit: Optional[int],
        enabled_file_types: Optional[List[str]],
        enabled_scraper: Optional[str],
    ) -> None:
        """Record that a parsing run has started."""
        event = StartedParsingStatus(
            system_timestamp=_now(),
            limit=limit,
            scraper=enabled_scraper,
            files_types=enabled_file_types,
            task_id=self.task_id,
        )
        self.database.insert_document("global_status", event.dict())

    def register_skipped_file(
        self, dump_file: DumpFile, content_sha256: Optional[str] = None
    ) -> None:
        """Record that a file was skipped because it is not readable."""
        event = SkippedFileStatus(
            system_timestamp=_now(),
            task_id=self.task_id,
            **self._dumpfile_to_event_fields(dump_file),
        )
        self.database.insert_document("events", event.dict())
        self._record_parsed_file(dump_file, None, content_sha256)

        fields = self._dumpfile_to_execution_log_fields(dump_file)
        fields.update({"loaded": False, "succusfull": None})
        self._file_logs.append(FileExecutionLog(**fields))

    def registered_file_to_process(self, dump_file: DumpFile) -> None:
        """Record that a file was registered to be processed."""
        event = RegisteredFileToProcessStatus(
            system_timestamp=_now(),
            task_id=self.task_id,
            **self._dumpfile_to_event_fields(dump_file),
        )
        self.database.insert_document("events", event.dict())

    def register_processed_file(
        self,
        dump_file: DumpFile,
        row_count: int,
        content_sha256: Optional[str] = None,
    ) -> None:
        """Record that a file was parsed successfully."""
        event = ProcessedFileStatus(
            system_timestamp=_now(),
            row_count=row_count,
            task_id=self.task_id,
            **self._dumpfile_to_event_fields(dump_file),
        )
        self.database.insert_document("events", event.dict())
        self._record_parsed_file(dump_file, row_count, content_sha256)

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
            system_timestamp=_now(),
            row_count=row_count,
            error=str(error),
            trace=trace,
            task_id=self.task_id,
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
        enabled_file_types: str,
        had_errors: bool,
        output_path: str,
        total_files: int,
    ) -> None:
        """Record that the parsing run has finished."""
        event = CompletedParsingStatus(
            system_timestamp=_now(),
            store_name=enabled_scraper,
            files_types=enabled_file_types,
            had_errors=had_errors,
            output_path=output_path,
            total_files=total_files,
            task_id=self.task_id,
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
