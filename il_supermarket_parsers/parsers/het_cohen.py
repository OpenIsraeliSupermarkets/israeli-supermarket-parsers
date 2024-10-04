from il_supermarket_parsers.engines import BigIdBranchesFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class HetChoenFileConverter(BigIdBranchesFileConverter):
    """het cohen converter"""

    def __init__(self):
        super().__init__(
            stores_parser=XmlDataFrameConverter(
                list_key="Branches",
                id_field="StoreID",
                roots=[],
            ),
            promo_parser=XmlDataFrameConverter(
                list_key="Sales",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PriceUpdateDate"],
            ),
            promofull_parser=XmlDataFrameConverter(
                list_key="Sales",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PriceUpdateDate"],
            ),
        )
