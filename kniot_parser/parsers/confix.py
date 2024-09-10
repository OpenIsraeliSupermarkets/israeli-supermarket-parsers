from kniot_parser.engines import BaseFileConverter
from kniot_parser.documents import XmlDataFrameConverter


class CofixFileConverter(BaseFileConverter):
    def __init__(self) -> None:
        super().__init__()
        self.price = XmlDataFrameConverter(
            list_key="Items",
            id_field=["ItemCode", "PriceUpdateDate", "ItemId"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
        self.pricefull = XmlDataFrameConverter(
            list_key="Items",
            id_field=["ItemCode", "PriceUpdateDate", "ItemId"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
