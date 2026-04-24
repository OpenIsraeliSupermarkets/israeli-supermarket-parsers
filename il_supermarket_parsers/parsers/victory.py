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


class VictoryNewFileConverter(BigIdBranchesFileConverter):
    """ויקטורי חדש"""

    def __init__(self):
        super().__init__(
            price_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            ),
            pricefull_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            ),
            promo_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PromotionUpdateTime"],
            ),
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PromotionUpdateTime"],
            ),
        )
