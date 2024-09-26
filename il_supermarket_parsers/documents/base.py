from abc import ABC, abstractmethod
import os
from il_supermarket_parsers.utils import build_value, get_root



class XmlBaseConverter(ABC):
    """parser the xml docuement"""

    def __init__(
        self,
        list_key,
        id_field,
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
    def validate_succussful_extraction(self, data, source_file):
        """validate column requested"""

    @abstractmethod
    def reduce_size(self, data):
        """reduce the size"""

    def build_value(self, name, no_content):
        """get the value """
        return build_value(name, self.additional_constant, no_content=no_content)

    def convert(
        self, found_store, file_name, no_content="NO-CONTENT", row_limit=None, **kwarg
    ):
        """parse file to data frame"""
        source_file = os.path.join(found_store, file_name)
        root, root_store = get_root(source_file, self.list_key, self.roots)

        data = self._phrse(
            root,
            found_store,
            file_name,
            root_store,
            no_content,
            row_limit=row_limit,
            **kwarg,
        )
        return self.reduce_size(data)  # self._normlize_columns(data, **kwarg)

    @abstractmethod
    def _phrse(
        self,
        root,
        found_folder,
        file_name,
        root_store,
        no_content,
        row_limit=None,
        **kwarg,
    ):
        pass

    @abstractmethod
    def _normlize_columns( self,
        data,
        missing_columns_default_values,
        columns_to_remove,
        columns_to_rename,
        date_columns=None,
        float_columns=None,
        empty_value="NOT_APPLY",
        **kwarg):
        pass
