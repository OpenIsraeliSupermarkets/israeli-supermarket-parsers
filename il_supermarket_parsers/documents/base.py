from abc import ABC, abstractmethod
from typing import List
import os
from il_supermarket_parsers.utils import build_value, get_root


class XmlBaseConverter(ABC):
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

    @abstractmethod
    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None
    ):
        """validate column requested"""

    @abstractmethod
    def reduce_size(self, data):
        """reduce the size"""

    def build_value(self, name, no_content):
        """get the value"""
        return build_value(name, self.additional_constant, no_content=no_content)

    def convert(self, found_store, file_name, **kwarg):
        """parse file to data frame"""
        source_file = os.path.join(found_store, file_name)
        root, root_store = get_root(source_file, self.list_key, self.roots)

        data = self._phrse(
            root,
            found_store,
            file_name,
            root_store,
            **kwarg,
        )
        return self.reduce_size(data)

    @abstractmethod
    def _phrse(
        self,
        root,
        found_folder,
        file_name,
        root_store,
        **kwarg,
    ):
        pass
