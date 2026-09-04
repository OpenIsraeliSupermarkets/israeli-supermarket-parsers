import os
from typing import AsyncIterator, Optional, Sequence, Union

from .base import XmlBaseConverter
from ..utils import (
    get_root_and_search,
    get_root_and_search_from_content,
)


class FirstPresentXmlDataFrameConverter(XmlBaseConverter):
    """Use the first converter whose list wrapper is present in the XML.

    Earlier options are probed in order using each converter's ``list_key``.
    The last option is the legacy fallback and always runs when none of the
    preceding wrappers exist, so older dumps keep parsing.
    """

    def __init__(self, options: Sequence[XmlBaseConverter]):
        """
        Initialize an N-way first-present converter.

        Args:
            options: Ordered converters (at least two). Each candidate except
                the last must expose ``list_key``, which is used as the
                presence check. The last converter is the fallback.
        """
        self.options = list(options)
        if len(self.options) < 2:
            raise ValueError(
                "FirstPresentXmlDataFrameConverter requires at least two "
                "converters (candidates plus a fallback)"
            )
        for option in self.options[:-1]:
            if not getattr(option, "list_key", None):
                raise ValueError(
                    "Each candidate converter must expose list_key "
                    "for the presence check"
                )

    def _key_is_present(self, option, found_store, file_name, file_content):
        """True when ``option.list_key`` exists in the XML."""
        roots = getattr(option, "roots", None)
        if file_content is not None:
            path_for_recovery = (
                os.path.join(found_store, file_name)
                if isinstance(found_store, str)
                else None
            )
            root_elem, _ = get_root_and_search_from_content(
                file_content,
                option.list_key,
                roots,
                file_path=path_for_recovery,
            )
        else:
            source_file = os.path.join(found_store, file_name)
            root_elem, _ = get_root_and_search(source_file, option.list_key, roots)
        return root_elem is not None

    def _pick_parser(self, found_store, file_name, file_content=None):
        """Return the first converter whose wrapper is present, else fallback."""
        *candidates, fallback = self.options
        for option in candidates:
            if self._key_is_present(option, found_store, file_name, file_content):
                return option
        return fallback

    async def convert(
        self,
        found_store: Union[str, bytes],
        file_name: str,
        file_content: Optional[bytes] = None,
        **kwarg,
    ) -> AsyncIterator[dict]:
        """reduce the size"""
        parser = self._pick_parser(found_store, file_name, file_content)
        async for row in parser.convert(
            found_store, file_name, file_content=file_content, **kwarg
        ):
            yield row

    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None
    ):
        """validate column requested"""
        found_store, file_name = os.path.split(source_file)
        parser = self._pick_parser(found_store, file_name)
        parser.validate_succussful_extraction(data, source_file, ignore_missing_columns)
