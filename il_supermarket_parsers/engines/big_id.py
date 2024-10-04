from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
)
from .base import BaseFileConverter


class BigIDFileConverter(BaseFileConverter):
    """a converter to all documents with ID instead of Id"""

    def __init__(
        self,
        pricefull_parser=None,
        price_parser=None,
        stores_parser=None,
        promofull_parser=None,
        promo_parser=None,
    ):
        super().__init__(
            pricefull_parser=(
                pricefull_parser
                if pricefull_parser
                else XmlDataFrameConverter(
                    list_key="Products",
                    id_field="ItemCode",
                    roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                )
            ),
            price_parser=(
                price_parser
                if price_parser
                else XmlDataFrameConverter(
                    list_key="Products",
                    id_field="ItemCode",
                    roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                )
            ),
            promo_parser=(
                promo_parser
                if promo_parser
                else XmlDataFrameConverter(
                    list_key="Sales",
                    id_field="ItemCode",
                    roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                )
            ),
            promofull_parser=(
                promofull_parser
                if promofull_parser
                else XmlDataFrameConverter(
                    list_key="Sales",
                    id_field="PromotionID",
                    roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                )
            ),
            stores_parser=(
                stores_parser
                if stores_parser
                else XmlDataFrameConverter(
                    list_key="Sales",
                    id_field="PromotionID",
                    roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                )
            ),
        )
