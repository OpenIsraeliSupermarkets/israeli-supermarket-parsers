import pandas as pd
from il_supermarket_parsers.utils import (
    count_tag_in_xml,
    collect_unique_keys_from_xml,
    collect_unique_columns_from_nested_json,
)
from .base import XmlBaseConverter


class ConditionalXmlDataFrameConverter(XmlBaseConverter):
    """parser the xml docuement"""

    def __init__(self, try_parser, catch_parser):
        self.try_parser = try_parser
        self.catch_parser = catch_parser

    def convert(self, found_store, file_name, **kwarg):
        """reduce the size"""
        try:
            return self.try_parser.convert(found_store, file_name, **kwarg)
        except:
            return self.catch_parser.convert(found_store, file_name, **kwarg)

    def validate_succussful_extraction(
        self, data, source_file, ignore_missing_columns=None
    ):
        """validate column requested"""
        try:
            self.try_parser.validate_succussful_extraction(
                data, source_file, ignore_missing_columns
            )
        except ValueError:
            self.catch_parser.validate_succussful_extraction(
                data, source_file, ignore_missing_columns
            )
