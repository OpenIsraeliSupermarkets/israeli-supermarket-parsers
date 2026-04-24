from il_supermarket_parsers.engines import BigIdBranchesFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
)


class VictoryFileConverter(BigIdBranchesFileConverter):
    """ויקטורי"""

    def __init__(self):
        super().__init__(
            stores_parser=XmlDataFrameConverter(
                list_key="Store",
                id_field="StoreID",
                roots=[],
            )
        )
        self.promofull_parser = XmlDataFrameConverter(
            list_key="Sales",
            id_field="PromotionID",
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )


class VictoryNewSourceFileConverter(VictoryFileConverter):
    """ויקטורי - מקור חדש"""

    def __init__(self):
        super().__init__()
        roots = ["ChainID", "SubChainID", "StoreID", "BikoretNo"]
        self.price_parser = XmlDataFrameConverter(
            list_key="Items",
            id_field="ItemCode",
            roots=roots,
        )
        self.pricefull_parser = XmlDataFrameConverter(
            list_key="Items",
            id_field="ItemCode",
            roots=roots,
        )
        self.promo_parser = XmlDataFrameConverter(
            list_key="Promotions",
            id_field="PromotionID",
            roots=roots,
        )
        self.promofull_parser = XmlDataFrameConverter(
            list_key="Promotions",
            id_field="PromotionID",
            roots=roots,
        )
        self.stores_parser = SubRootedXmlDataFrameConverter(
            list_key="SubChains",
            sub_roots=["SubChainId", "SubChainName"],
            id_field="StoreID",
            list_sub_key="Stores",
            roots=["ChainID", "ChainName", "LastUpdateDate", "LastUpdateTime"],
        )
