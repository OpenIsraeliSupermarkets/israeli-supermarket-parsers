from __future__ import annotations

from typing import Optional

from il_supermarket_parsers.engines import BaseFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
)


class CofixFileConverter(BaseFileConverter):
    "Confix converter"

    def __init__(self, promofull_parser: Optional[XmlDataFrameConverter] = None) -> None:
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
            promofull_parser=promofull_parser
            if promofull_parser
            else XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
            stores_parser=SubRootedXmlDataFrameConverter(
                list_key="SubChains",
                id_field="StoreId",
                options=SubRootedXmlOptions(
                    roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                    list_sub_key="Stores",
                    sub_roots=["SubChainName", "SubChainId"],
                    ignore_column=["XmlDocVersion"],
                ),
            ),
        )
