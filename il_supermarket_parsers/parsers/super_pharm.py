from il_supermarket_parsers.engines import BigIDFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class SuperPharmFileConverter(BigIDFileConverter):
    """for super-pharam"""

    def __init__(self):
        super().__init__()

        self.promofull_parser = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Details",
            id_field=["PromotionId", "PriceUpdateDate", "ItemCode"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
        self.promo_parser = XmlDataFrameConverter(
            list_key="Details",
            id_field=["PromotionId", "PriceUpdateDate", "ItemCode"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )

        self.pricefull_parser = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Details",
            id_field=["ItemCode"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
        self.price_parser = XmlDataFrameConverter(
            list_key="Details",
            id_field=["ItemCode", "PriceUpdateDate"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
        self.stores_parser = XmlDataFrameConverter(
            list_key="Details",
            id_field=["StoreId"],
            roots=["ChainId", "SubChainId"],
        )
