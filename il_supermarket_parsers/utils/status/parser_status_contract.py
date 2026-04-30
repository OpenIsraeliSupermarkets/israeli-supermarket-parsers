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
    when: Optional[datetime] = None
    limit: Optional[int] = None
    scraper: Optional[str] = None
    files_types: Optional[List[str]] = None
    task_id: Optional[str] = None


class CompletedParsingStatus(BaseModel):
    """Status event recorded when a parsing run finishes."""

    status: str = "completed"
    when: Optional[datetime] = None
    store_name: Optional[str] = None
    files_types: Optional[List[str]] = None
    had_errors: bool = False
    output_path: Optional[str] = None
    total_files: int = 0
    task_id: Optional[str] = None


# -- Per-file events --


class ProcessedFileStatus(BaseModel):
    """Event recorded when a file is parsed successfully."""

    status: str = "processed"
    when: Optional[datetime] = None
    file_name: str
    store_folder: str
    file_type: str
    row_count: int
    task_id: Optional[str] = None


class SkippedFileStatus(BaseModel):
    """Event recorded when a file is skipped (not readable / empty)."""

    status: str = "skipped"
    when: Optional[datetime] = None
    file_name: str
    store_folder: str
    file_type: str
    task_id: Optional[str] = None


class FailedFileStatus(BaseModel):
    """Event recorded when a file fails during processing."""

    status: str = "failed"
    when: Optional[datetime] = None
    file_name: str
    store_folder: str
    file_type: str
    error: str
    trace: str
    row_count: int = 0
    task_id: Optional[str] = None


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
    events: List[Union[ProcessedFileStatus, SkippedFileStatus, FailedFileStatus]] = (
        Field(default_factory=list)
    )

    def validate_parsing_run(self) -> Tuple[bool, str]:
        """Validate that the stored events form a coherent lifecycle.

        Rules:
        - Must contain exactly one 'started' global event.
        - Must contain exactly one 'completed' global event.
        - Each file must appear in exactly one per-file event.

        Returns:
            (True, "") on success or (False, reason_str) on failure.
        """
        reason = self._started_completed_errors()
        if reason is not None:
            return False, reason
        reason = self._per_file_unique_errors()
        if reason is not None:
            return False, reason
        reason = self._limit_and_totals_errors()
        if reason is not None:
            return False, reason
        return True, ""

    def _started_completed_errors(self) -> Optional[str]:
        started_events = [
            e for e in self.global_status if isinstance(e, StartedParsingStatus)
        ]
        completed_events = [
            e for e in self.global_status if isinstance(e, CompletedParsingStatus)
        ]

        if not started_events:
            return "No 'started' event found"
        if len(started_events) > 1:
            return f"Multiple 'started' events found: {len(started_events)}"
        if not completed_events:
            return "No 'completed' event found"
        if len(completed_events) > 1:
            return f"Multiple 'completed' events found: {len(completed_events)}"
        return None

    def _per_file_unique_errors(self) -> Optional[str]:
        per_file: dict = defaultdict(list)
        for event in self.events:
            per_file[event.file_name].append(event.status)

        for file_name, statuses in per_file.items():
            if len(statuses) > 1:
                return f"File '{file_name}' has multiple events: {statuses}"
        return None

    def _limit_and_totals_errors(self) -> Optional[str]:
        started_events = [
            e for e in self.global_status if isinstance(e, StartedParsingStatus)
        ]
        completed_events = [
            e for e in self.global_status if isinstance(e, CompletedParsingStatus)
        ]
        started = started_events[0]
        completed = completed_events[0]
        processed_count = sum(
            1 for e in self.events if isinstance(e, ProcessedFileStatus)
        )

        if started.limit is not None and started.limit > 0:
            if processed_count > started.limit:
                return (
                    f"Processed {processed_count} files but limit was {started.limit}"
                )

        if completed.total_files != len(self.events):
            return (
                f"completed.total_files={completed.total_files} but "
                f"{len(self.events)} file events recorded"
            )
        return None
