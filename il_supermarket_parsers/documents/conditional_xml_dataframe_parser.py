import os
from typing import AsyncIterator, Optional, Union

from .base import XmlBaseConverter
from ..utils import (
    get_root,
    get_root_and_search,
    get_root_and_search_from_content,
    get_root_from_content,
)


class ConditionalXmlDataFrameConverter(XmlBaseConverter):
    """parser the xml docuement"""

    def __init__(self, option_a, option_b, root_value=None, check_key=None):
        """
        Initialize conditional converter.

        Args:
            option_a: Parser to use when condition is true
            option_b: Parser to use when condition is false
            root_value: If provided, checks if root.tag == root_value (legacy behavior)
            check_key: If provided, checks if element with this key exists
                (checks option_a's list_key)
        """
        self.option_a = option_a
        self.option_b = option_b
        self.root_value = root_value
        self.check_key = check_key

    def _pick_parser(self, found_store, file_name, file_content):
        """Return option_a or option_b based on XML structure (sync helpers)."""
        if self.check_key is not None:
            roots = getattr(self.option_a, "roots", None)
            if file_content is not None:
                path_for_recovery = (
                    os.path.join(found_store, file_name)
                    if isinstance(found_store, str)
                    else None
                )
                root_elem, _ = get_root_and_search_from_content(
                    file_content,
                    self.check_key,
                    roots,
                    file_path=path_for_recovery,
                )
            else:
                source_file = os.path.join(found_store, file_name)
                root_elem, _ = get_root_and_search(
                    source_file, self.check_key, roots
                )
            return self.option_a if root_elem is not None else self.option_b

        path_hint = (
            os.path.join(found_store, file_name)
            if isinstance(found_store, str)
            else None
        )
        if file_content is not None:
            root = get_root_from_content(file_content, file_path=path_hint)
        else:
            source_file = os.path.join(found_store, file_name)
            root = get_root(source_file)
        return self.option_a if root.tag == self.root_value else self.option_b

    async def convert(
        self,
        found_store: Union[str, bytes],
        file_name: str,
        file_content: Optional[bytes] = None,
        **kwarg,
    ) -> AsyncIterator[dict]:
        """reduce the size"""
        if self.check_key is None and self.root_value is None:
            raise ValueError("Either check_key or root_value must be set")

        parser = self._pick_parser(found_store, file_name, file_content)
        async for row in parser.convert(
            found_store, file_name, file_content=file_content, **kwarg
        ):
            yield row

    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None
    ):
        """validate column requested"""
        # If check_key is provided, check for element existence instead of root tag
        if self.check_key is not None:
            root_elem, _ = get_root_and_search(
                source_file, self.check_key, getattr(self.option_a, "roots", None)
            )
            if root_elem is not None:
                self.option_a.validate_succussful_extraction(
                    data, source_file, ignore_missing_columns
                )
            else:
                self.option_b.validate_succussful_extraction(
                    data, source_file, ignore_missing_columns
                )
        else:
            root = get_root(source_file)
            if root.tag == self.root_value:
                self.option_a.validate_succussful_extraction(
                    data, source_file, ignore_missing_columns
                )
            else:
                self.option_b.validate_succussful_extraction(
                    data, source_file, ignore_missing_columns
                )
