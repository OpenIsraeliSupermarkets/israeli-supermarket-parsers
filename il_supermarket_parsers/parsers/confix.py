from il_supermarket_parsers.engines import BaseFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
)


class CofixFileConverter(BaseFileConverter):
    "Confix converter"

    def __init__(self) -> None:
        super().__init__(
            price_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
            pricefull_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
            promo_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
            stores_parser=SubRootedXmlDataFrameConverter(
                id_field="StoreId",
                list_key="SubChains",
                roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                list_sub_key="Stores",
                sub_roots=["SubChainName", "SubChainId"],
                ignore_column=["XmlDocVersion"],
            ),
        )
