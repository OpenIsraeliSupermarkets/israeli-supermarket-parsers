from kniot_parser.engines import BaseFileConverter
from kniot_parser.documents import XmlDataFrameConverter


class SalachDabachFileConverter(BaseFileConverter):
    def __init__(self) -> None:
        super().__init__()
        self.price_parser = XmlDataFrameConverter(
            list_key="Items",
            id_field=["ItemCode", "PriceUpdateDate", "ItemId"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
        self.pricefull_parser = XmlDataFrameConverter(
            list_key="Items",
            id_field=["ItemCode", "PriceUpdateDate", "ItemId"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
