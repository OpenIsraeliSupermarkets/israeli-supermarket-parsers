from abc import ABC
from kniot_parser.documents import (
    XmlBaseConverter,
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
)


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
                full_data_snapshot=True,
                list_key="Items",
                id_field=["ItemCode", "PriceUpdateDate"],
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            )
        )
        self.promofull: XmlBaseConverter = (
            promofull_parser
            if promofull_parser
            else XmlDataFrameConverter(
                full_data_snapshot=True,
                list_key="Promotions",
                id_field=["PromotionId"],
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
            )
        )
        self.stores: XmlBaseConverter = (
            stores_parser
            if stores_parser
            else SubRootedXmlDataFrameConverter(
                full_data_snapshot=True,
                list_key="SubChains",
                sub_roots=["SubChainId", "SubChainName"],
                id_field=["StoreId"],
                list_sub_key="Stores",
                roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                renames={
                    "LastUpdateDate": "DocLastUpdateDate",
                    "LastUpdateTime": "DocLastUpdateTime",
                },
            )
        )
        self.price: XmlBaseConverter = (
            price_parser
            if price_parser
            else XmlDataFrameConverter(
                list_key="Items",
                id_field=["ItemCode", "PriceUpdateDate"],
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            )
        )
        self.promo: XmlBaseConverter = (
            promo_parser
            if promo_parser
            else XmlDataFrameConverter(
                list_key="Promotions",
                id_field=["PromotionId", "PromotionUpdateDate"],
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
            )
        )

    def get(self, file_type):
        """get parser by file type"""
        return getattr(self, file_type)
