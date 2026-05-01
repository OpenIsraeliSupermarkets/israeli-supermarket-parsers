"""Data classes defining the output format contract for parser status.

Mirrors il_supermarket_scarper.utils.scraper_status_contract.
"""

# Pydantic models are data-only; min-public-methods in pylint is not applicable.
# pylint: disable=too-few-public-methods

from collections import defaultdict
from datetime import datetime
from typing import List, Optional, Tuple, Union

from pydantic import BaseModel, Field


# -- Global status events --
class StartedParsingStatus(BaseModel):
    """Status event recorded when a parsing run begins."""

    status: str = "started"
    system_timestamp: datetime
    limit: Optional[int] = None
    scraper: str
    files_types: str
    task_id: str


class CompletedParsingStatus(BaseModel):
    """Status event recorded when a parsing run finishes."""

    status: str = "completed"
    system_timestamp: datetime
    store_name: str
    files_types: str
    had_errors: bool = False
    output_path: str
    total_files: int = 0
    task_id: str


# -- Per-file events --


class ProcessedFileStatus(BaseModel):
    """Event recorded when a file is parsed successfully."""

    status: str = "processed"
    system_timestamp: datetime
    file_name: str
    store_folder: str
    file_type: str
    row_count: int
    task_id: str


class RegisteredFileToProcessStatus(BaseModel):
    """Event recorded when a file is registered to be processed."""

    status: str = "registered"
    system_timestamp: datetime
    file_name: str
    store_folder: str
    file_type: str
    task_id: str


class SkippedFileStatus(BaseModel):
    """Event recorded when a file is skipped (not readable / empty)."""

    status: str = "skipped"
    system_timestamp: datetime
    file_name: str
    store_folder: str
    file_type: str
    task_id: str


class FailedFileStatus(BaseModel):
    """Event recorded when a file fails during processing."""

    status: str = "failed"
    system_timestamp: datetime
    file_name: str
    store_folder: str
    file_type: str
    error: str
    trace: str
    row_count: int = 0
    task_id: str


# -- Aggregate output --


class ParserStatusOutput(BaseModel):
    """Complete output format for a single parser status database.

    Structure mirrors ScraperStatusOutput:
    - global_status: started + completed events for the run
    - events: one entry per file (processed, skipped, or failed)
    """

    global_status: List[Union[StartedParsingStatus, CompletedParsingStatus]] = Field(
        default_factory=list
    )
    events: List[
        Union[
            RegisteredFileToProcessStatus,
            SkippedFileStatus,
            ProcessedFileStatus,
            FailedFileStatus,
        ]
    ] = Field(default_factory=list)

    def _build_per_file_status_data(self):
        """Build per-file status records and status counters.

        Returns:
            A tuple of (per_file_dict, per_file_status_counter_dict)
            - per_file_dict: Maps file name to status flags
                (registered, processed, skipped, failed)
            - per_file_status_counter_dict: Maps file name to list of status
                types for duplicate detection
        """
        per_file = defaultdict(
            lambda: {
                "registered": False,
                "processed": False,
                "skipped": False,
                "failed": False,
            }
        )
        per_file_status_counter = defaultdict(list)

        for event in self.events:
            if isinstance(event, RegisteredFileToProcessStatus):
                fn = event.file_name
                per_file[fn]["registered"] = True
                per_file_status_counter[fn].append("registered")
            elif isinstance(event, ProcessedFileStatus):
                fn = event.file_name
                per_file[fn]["processed"] = True
                per_file_status_counter[fn].append("processed")
            elif isinstance(event, SkippedFileStatus):
                fn = event.file_name
                per_file[fn]["skipped"] = True
                per_file_status_counter[fn].append("skipped")
            elif isinstance(event, FailedFileStatus):
                fn = event.file_name
                per_file[fn]["failed"] = True
                per_file_status_counter[fn].append("failed")

        return per_file, per_file_status_counter

    @staticmethod
    def _validate_file_lifecycle(status: dict) -> bool:
        """Validate a single file's lifecycle.

        Rules:
        - Must be registered.
        - processed, skipped, or failed each require a prior registered event.
        """
        if not status["registered"]:
            return False
        return True

    @staticmethod
    def _has_duplicate_statuses(status_counter_list: list) -> bool:
        """Check if a file has duplicate status types."""
        from collections import Counter  # pylint: disable=import-outside-toplevel

        status_counter = Counter(status_counter_list)
        for count in status_counter.values():
            if count > 1:
                return True
        return False

    def validate_file_status(self) -> bool:
        """Validate that every attempted file has a coherent lifecycle.

        Ensures that for every file that was processed, skipped, or failed,
        there is a 'registered' event. Also checks that no file appears
        under the same status type more than once.

        Files that were only registered but never resolved are not validated,
        as they may have been deferred due to limit constraints.
        """
        per_file, per_file_status_counter = self._build_per_file_status_data()

        for fn, status in per_file.items():
            if status["registered"] and not (
                status["processed"] or status["skipped"] or status["failed"]
            ):
                continue

            if not self._validate_file_lifecycle(status):
                return False
            if self._has_duplicate_statuses(per_file_status_counter[fn]):
                return False

        return True
