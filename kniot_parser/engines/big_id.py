from kniot_parser.documents import (
    XmlDataFrameConverter,
)
from .base import BaseFileConverter


class BigIDFileConverter(BaseFileConverter):
    """a converter to all documents with ID instead of Id"""

    def __init__(self):
        super().__init__()
        self.pricefull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Products",
            id_field=["ItemCode", "PriceUpdateDate"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
        )
        self.price = XmlDataFrameConverter(
            list_key="Products",
            id_field=["ItemCode", "PriceUpdateDate"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
        )
        self.promo = XmlDataFrameConverter(
            list_key="Sales",
            id_field=["ItemCode", "PriceUpdateDate"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
        self.promofull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Sales",
            id_field=["PromotionId", "ItemCode"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
        self.stores = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Sales",
            id_field=["ItemCode", "PromotionUpdateDate"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
