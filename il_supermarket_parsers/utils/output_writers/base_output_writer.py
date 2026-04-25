from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import FileCompleteMessage
    from ..loading_utils import DumpFile


class BaseOutputWriter(ABC):
    """Abstract base class for output writers"""

    @abstractmethod
    async def write_row(self, row: dict) -> None:
        """
        Write a single row to output

        Args:
            row: Dictionary representing a single row
        """
        raise NotImplementedError

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the output writer (e.g., create file, detect columns)
        Called before first row is written
        """
        raise NotImplementedError

    @abstractmethod
    async def initialize_new_file(self, file: DumpFile) -> None:
        """
        Initialize the output writer for a new file

        Args:
            file: File object
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self) -> bool:
        """
        Check if output already exists

        Returns:
            True if output exists, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_path(self) -> str:
        """
        Get the path/identifier for this output

        Returns:
            Path or identifier string
        """
        raise NotImplementedError

    @abstractmethod
    def get_existing_columns(self) -> List[str]:
        """
        Get existing columns from output for alignment

        Returns:
            List of column names, empty list if output doesn't exist
        """
        raise NotImplementedError

    async def write_file_complete(self, _message: "FileCompleteMessage") -> None:
        """Signal that all rows for a file have been written. No-op by default."""
        return

    @abstractmethod
    def close(self) -> None:
        """Close the output writer"""
        raise NotImplementedError
