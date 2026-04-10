from abc import ABC, abstractmethod
from typing import List, Optional


class BaseOutputWriter(ABC):
    """Abstract base class for output writers"""

    @abstractmethod
    async def write_row(self, row: dict) -> None:
        """
        Write a single row to output

        Args:
            row: Dictionary representing a single row
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the output writer (e.g., create file, detect columns)
        Called before first row is written
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """
        Check if output already exists

        Returns:
            True if output exists, False otherwise
        """
        pass

    @abstractmethod
    def get_path(self) -> str:
        """
        Get the path/identifier for this output

        Returns:
            Path or identifier string
        """
        pass

    @abstractmethod
    def get_existing_columns(self) -> List[str]:
        """
        Get existing columns from output for alignment

        Returns:
            List of column names, empty list if output doesn't exist
        """
        pass
