from abc import ABC
import os
from il_supermarket_scarper import FileTypesFilters
from il_supermarket_parsers.documents import (
    XmlBaseConverter,
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
)
from il_supermarket_parsers.utils import DumpFile


class BaseFileConverter(ABC):
    """abstract parser"""

    def __init__(
        self,
        pricefull_parser: XmlBaseConverter = None,
        promofull_parser: XmlBaseConverter = None,
        stores_parser: XmlBaseConverter = None,
        price_parser: XmlBaseConverter = None,
        promo_parser: XmlBaseConverter = None,
    ) -> None:
        self.pricefull_parser = (
            pricefull_parser
            if pricefull_parser
            else XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            )
        )
        self.promofull_parser: XmlBaseConverter = (
            promofull_parser
            if promofull_parser
            else XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            )
        )
        self.stores_parser: XmlBaseConverter = (
            stores_parser
            if stores_parser
            else SubRootedXmlDataFrameConverter(
                list_key="SubChains",
                sub_roots=["SubChainId", "SubChainName"],
                id_field="StoreId",
                list_sub_key="Stores",
                roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            )
        )
        self.price_parser: XmlBaseConverter = (
            price_parser
            if price_parser
            else XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            )
        )
        self.promo_parsers: XmlBaseConverter = (
            promo_parser
            if promo_parser
            else XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            )
        )
            
        
    def _load_parser(self,dump_file:DumpFile):
        parser_mapping = {
            FileTypesFilters.PRICE_FILE: self.price_parser,
            FileTypesFilters.PRICE_FULL_FILE: self.pricefull_parser,
            FileTypesFilters.PROMO_FILE: self.promo_parsers,
            FileTypesFilters.PROMO_FULL_FILE: self.promofull_parser,
            FileTypesFilters.STORE_FILE: self.stores_parser,
        }

        parser = parser_mapping.get(dump_file.detected_filetype)
        if parser is None:
            # TODO: add a logger
            # TODO: make error more specific
            raise ValueError("Something went wrong")

    def read(self, dump_file: DumpFile, run_validation=False):
        """covert the dump file to the target format according to the filetype"""
        parser = self._load_parser(dump_file)

        data = parser.convert(
            dump_file.store_folder,
            dump_file.file_name,
            column_config_mapping=self.load_column_config(settings)
        )

        if run_validation:
            source_file = os.path.join(dump_file.store_folder, dump_file.file_name)
            parser.validate_succussful_extraction(data, source_file)
        return data
