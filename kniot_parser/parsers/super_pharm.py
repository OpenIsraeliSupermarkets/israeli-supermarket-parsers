from kniot_parser.engines import BigIDFileConverter
from kniot_parser.documents import XmlDataFrameConverter


class SuperPharmFileConverter(BigIDFileConverter):
    """for super-pharam"""

    def __init__(self):
        super().__init__()

        self.promofull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Details",
            id_field=["PromotionId", "PriceUpdateDate", "ItemCode"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
        self.promo = XmlDataFrameConverter(
            list_key="Details",
            id_field=["PromotionId", "PriceUpdateDate", "ItemCode"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )

        self.pricefull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Details",
            id_field=["ItemCode"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
        self.price = XmlDataFrameConverter(
            list_key="Details",
            id_field=["ItemCode", "PriceUpdateDate"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
        self.stores = XmlDataFrameConverter(
            list_key="Details",
            id_field=["StoreId"],
            roots=["ChainId", "SubChainId"],
        )
