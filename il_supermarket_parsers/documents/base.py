from abc import ABC, abstractmethod
from typing import List, AsyncIterator, Union, Optional
import os
from il_supermarket_parsers.utils import (
    build_value, 
    get_root_and_search, 
    get_root_and_search_from_content,
)


class XmlBaseConverter(ABC):
    """parser the xml docuement"""

    @abstractmethod
    async def convert(
        self, 
        found_store: Union[str, bytes], 
        file_name: str, 
        file_content: Optional[bytes] = None,
        **kwarg
    ) -> AsyncIterator[dict]:
        """parse file to async generator of row dicts"""

    @abstractmethod
    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None
    ):
        """validate column requested"""


class BaseXMLParser(XmlBaseConverter, ABC):
    """parser the xml docuement"""

    def __init__(
        self,
        list_key: List[str],
        id_field: str,
        roots=None,
        ignore_column=None,
        **additional_constant,
    ):
        self.list_key = list_key
        self.roots = roots
        self.id_field = id_field
        self.ignore_column = ignore_column if ignore_column else []
        self.additional_constant = additional_constant

    def build_value(self, name, no_content):
        """get the value"""
        return build_value(name, self.additional_constant, no_content=no_content)

    async def convert(
        self, 
        found_store: Union[str, bytes], 
        file_name: str, 
        file_content: Optional[bytes] = None,
        **kwarg
    ) -> AsyncIterator[dict]:
        """parse file to async generator of row dicts

        Args:
            found_store: Directory containing the file, or file content if file_content is provided
            file_name: Name of the file to parse
            file_content: Optional file content as bytes (for queue-based files)
            **kwarg: Additional keyword arguments
        """
        # Determine if we're using file system or in-memory content
        if file_content is not None:
            # Queue-based file (in-memory)
            root, root_store = get_root_and_search_from_content(
                file_content, 
                self.list_key[0] if self.list_key else None, 
                self.roots
            )
            found_folder = found_store if isinstance(found_store, str) else "queue"
        else:
            # File system based
            source_file = os.path.join(found_store, file_name)
            root, root_store = get_root_and_search(source_file, self.list_key, self.roots)
            found_folder = found_store

        async for row in self._parse(
            root,
            found_folder,
            file_name,
            root_store,
            **kwarg,
        ):
            yield row

    @abstractmethod
    async def _parse(
        self,
        root,
        found_folder,
        file_name,
        root_store,
        **kwarg,
    ) -> AsyncIterator[dict]:
        """parse file to async generator of row dicts"""
