from il_supermarket_parsers.utils import build_value, get_root
from abc import ABC, abstractmethod


class XmlBaseConverter(ABC):
    """parser the xml docuement"""

    def __init__(
        self,
        list_key,
        id_field,
        roots=None,
        columns_to_renames=None,
        columns_to_drop=None,
        mandatory_columns=None,
        **additional_constant
    ):
        self.list_key = list_key
        self.roots = roots
        self.id_field = id_field
        self.columns_to_renames = columns_to_renames
        self.additional_constant = additional_constant
        self.columns_to_drop = columns_to_drop
        self.mandatory_columns = mandatory_columns

    # def get_id(self):
    #     """get the id in each entery of the list"""
    #     if isinstance(self.id_field, list):
    #         return self.id_field
    #     return [self.id_field]

    # def get_constant(self, value):
    #     """get constant"""
    #     return self.additional_constant.get(value, None)

    def build_value(self, name, no_content):
        return build_value(name, self.additional_constant, no_content=no_content)

    def convert(self, file, no_content="NO-CONTENT", row_limit=None, **kwarg):
        """parse file to data frame"""
        root, root_store = get_root(file, self.list_key, self.roots)

        data = self._phrse(
            root, file, root_store, no_content, row_limit=row_limit, **kwarg
        )
        return self._normlize_columns(data, **kwarg)

    @abstractmethod
    def _phrse(self, root, file, root_store, no_content, row_limit=None, **kwarg):
        pass

    @abstractmethod
    def _normlize_columns(self, data):
        pass
