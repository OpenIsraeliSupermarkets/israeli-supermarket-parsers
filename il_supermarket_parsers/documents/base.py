from abc import ABC, abstractmethod
from typing import List, AsyncIterator, Union, Optional
import os
from il_supermarket_parsers.utils import (
    build_value,
    get_root,
    get_root_from_content,
    search_root,
)


class XmlBaseConverter(ABC):
    """parser the xml docuement"""

    @abstractmethod
    async def convert(
        self,
        found_store: Union[str, bytes],
        file_name: str,
        file_content: Optional[bytes] = None,
        **kwarg,
    ) -> AsyncIterator[dict]:
        """parse file to async generator of row dicts"""

    @abstractmethod
    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None
    ):
        """validate column requested"""

    def verify_rows(self, rows: List[dict]) -> None:
        """Check the rows of the last :meth:`convert` against its XML.

        ``convert`` must have been called with ``keep_document=True``. Raises
        ``ValueError`` on any mismatch.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support extraction verification"
        )


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
        self._kept_document = None
        self._kept_source = None

    def build_value(self, name, no_content):
        """get the value"""
        return build_value(name, self.additional_constant, no_content=no_content)

    async def convert(
        self,
        found_store: Union[str, bytes],
        file_name: str,
        file_content: Optional[bytes] = None,
        **kwarg,
    ) -> AsyncIterator[dict]:
        """parse file to async generator of row dicts

        Args:
            found_store: Directory containing the file, or file content if file_content is provided
            file_name: Name of the file to parse
            file_content: Optional file content as bytes (for queue-based files)
            **kwarg: Additional keyword arguments. ``keep_document=True`` keeps
                the parsed XML so :meth:`verify_rows` can check the rows
                without parsing the file again.
        """
        keep_document = kwarg.pop("keep_document", False)
        self._kept_document = None
        self._kept_source = None
        # Determine if we're using file system or in-memory content
        if file_content is not None:
            # Queue-based file (in-memory)
            document = get_root_from_content(file_content)
            list_key = self.list_key if self.list_key else None
            found_folder = found_store if isinstance(found_store, str) else "queue"
        else:
            # File system based
            document = get_root(os.path.join(found_store, file_name))
            list_key = self.list_key
            found_folder = found_store
        root, root_store = search_root(document, list_key, self.roots)
        if keep_document:
            self._kept_document = document
            self._kept_source = os.path.join(found_folder, file_name)
        del document

        async for row in self._parse(
            root,
            found_folder,
            file_name,
            root_store,
            **kwarg,
        ):
            yield row

    def _take_kept_document(self):
        """Return the document kept by ``convert`` and release it."""
        if self._kept_document is None:
            raise RuntimeError(
                "verify_rows needs the document: call convert(..., keep_document=True)"
            )
        document, source = self._kept_document, self._kept_source
        self._kept_document = None
        self._kept_source = None
        return document, source

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
