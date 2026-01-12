from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class BaseOutputWriter(ABC):
    """Abstract base class for output writers"""

    @abstractmethod
    def write_batch(self, df: pd.DataFrame) -> None:
        """
        Write a batch (DataFrame) to output

        Args:
            df: DataFrame to write
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
