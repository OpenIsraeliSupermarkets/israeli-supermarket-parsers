from abc import ABC, abstractmethod
from typing import List
from .loading_utils import DumpFile


class BaseDataLoader(ABC):
    """Abstract base class for data loaders"""

    @abstractmethod
    def load(self, limit=None) -> List[DumpFile]:
        """
        Load dump files

        Args:
            limit: Optional limit on number of files to load

        Returns:
            List of DumpFile objects
        """
        pass
