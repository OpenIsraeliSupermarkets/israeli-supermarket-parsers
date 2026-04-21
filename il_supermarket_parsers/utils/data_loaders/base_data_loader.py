from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from ..loading_utils import DumpFile


class BaseDataLoader(ABC):
    """Abstract base class for data loaders"""

    @abstractmethod
    async def load(
        self,
        limit: Optional[int] = None,
        store_names: Optional[list] = None,
        files_types: Optional[list] = None,
    ) -> AsyncIterator[DumpFile]:
        """
        Load dump files as async generator

        Args:
            limit: Optional limit on number of files to load
            store_names: Optional list of store names to filter
            files_types: Optional list of file types to filter

        Yields:
            DumpFile objects as they are discovered
        """
        pass
