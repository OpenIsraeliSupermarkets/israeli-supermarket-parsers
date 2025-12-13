import os
from .base import XmlBaseConverter
from ..utils import get_root, get_root_and_search


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

    def convert(self, found_store, file_name, **kwarg):
        """reduce the size"""
        source_file = os.path.join(found_store, file_name)

        # If check_key is provided, check for element existence instead of root tag
        if self.check_key is not None:
            # Check if the element exists (using option_a's roots for context)
            root_elem, _ = get_root_and_search(
                source_file, self.check_key, getattr(self.option_a, "roots", None)
            )
            if root_elem is not None:
                return self.option_a.convert(found_store, file_name, **kwarg)
            return self.option_b.convert(found_store, file_name, **kwarg)

        root = get_root(source_file)
        if root.tag == self.root_value:
            return self.option_a.convert(found_store, file_name, **kwarg)
        return self.option_b.convert(found_store, file_name, **kwarg)

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
