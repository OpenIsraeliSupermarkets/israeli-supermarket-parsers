from il_supermarket_parsers.documents import (
    XmlBaseConverter,
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
)
from il_supermarket_scarper import FileTypesFilters
from il_supermarket_parsers.utils import DumpFile
from abc import ABC
import json
import os


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
                ignore_column=['XmlDocVersion', 'DllVerNo']

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
                ignore_column=['XmlDocVersion', 'DllVerNo']

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
                ignore_column=['XmlDocVersion', 'DllVerNo']

            )
        )
        self.price_parser: XmlBaseConverter = (
            price_parser
            if price_parser
            else XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=['XmlDocVersion', 'DllVerNo']
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
                ignore_column=['XmlDocVersion', 'DllVerNo']

            )
        )

    def load_column_config(self, json_key):
        with open("il_supermarket_parsers/conf/processing.json") as file:
            return json.load(file)[json_key]

    def read(self, dump_file: DumpFile):

        if dump_file.detected_filetype == FileTypesFilters.PRICE_FILE:
            parser = self.price_parser
            settings = "price"
        elif dump_file.detected_filetype == FileTypesFilters.PRICE_FULL_FILE:
            parser = self.pricefull_parser
            settings = "pricefull"

        elif dump_file.detected_filetype == FileTypesFilters.PROMO_FILE:
            parser = self.promo_parsers
            settings = "promo"

        elif dump_file.detected_filetype == FileTypesFilters.PROMO_FULL_FILE:
            parser = self.promofull_parser
            settings = "promofull"

        elif dump_file.detected_filetype == FileTypesFilters.STORE_FILE:
            parser = self.stores_parser
            settings = "store"
        else:
            raise ValueError("Something want wrong")

        return parser.convert(
            dump_file.store_folder,
            dump_file.file_name,
            **self.load_column_config(settings)
        )
