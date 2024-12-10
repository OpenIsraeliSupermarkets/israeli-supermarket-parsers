import os
from .base import XmlBaseConverter
from ..utils import get_root


class ConditionalXmlDataFrameConverter(XmlBaseConverter):
    """parser the xml docuement"""

    def __init__(self, option_a, option_b, root_value):
        self.option_a = option_a
        self.option_b = option_b
        self.root_value = root_value

    def convert(self, found_store, file_name, **kwarg):
        """reduce the size"""
        root = get_root(os.path.join(found_store, file_name))
        if root.tag == self.root_value:
            return self.option_a.convert(found_store, file_name, **kwarg)
        return self.option_b.convert(found_store, file_name, **kwarg)

    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None
    ):
        """validate column requested"""
        root = get_root(source_file)
        if root.tag == self.root_value:
            self.option_a.validate_succussful_extraction(
                data, source_file, ignore_missing_columns
            )
        else:
            self.option_b.validate_succussful_extraction(
                data, source_file, ignore_missing_columns
            )
