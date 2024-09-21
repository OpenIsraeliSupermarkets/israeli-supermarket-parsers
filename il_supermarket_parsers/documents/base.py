from il_supermarket_parsers.utils import build_value, get_root
from abc import ABC, abstractmethod
import os


class XmlBaseConverter(ABC):
    """parser the xml docuement"""

    def __init__(
        self,
        list_key,
        id_field,
        roots=None,
        ignore_column=[],
        **additional_constant,
    ):
        self.list_key = list_key
        self.roots = roots
        self.id_field = id_field
        self.ignore_column = ignore_column
        self.additional_constant = additional_constant


    @abstractmethod
    def validate_succussful_extraction(self, data, source_file):
       """validate column requested"""

    def build_value(self, name, no_content):
        return build_value(name, self.additional_constant, no_content=no_content)

    def convert(
        self, found_store, file_name, no_content="NO-CONTENT", row_limit=None, **kwarg
    ):
        """parse file to data frame"""
        source_file = os.path.join(found_store, file_name)
        root, root_store = get_root(
            source_file, self.list_key, self.roots
        )

        data = self._phrse(
            root,
            found_store,
            file_name,
            root_store,
            no_content,
            row_limit=row_limit,
            **kwarg,
        )

        self.validate_succussful_extraction(data,source_file)
        return data#self._normlize_columns(data, **kwarg)

    @abstractmethod
    def _phrse(
        self,
        root,
        found_store,
        file_name,
        root_store,
        no_content,
        row_limit=None,
        **kwarg,
    ):
        pass

    @abstractmethod
    def _normlize_columns(self, data):
        pass
