from il_supermarket_parsers.engines import BigIdBranchesFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class VictoryFileConverter(BigIdBranchesFileConverter):
    """ויקטורי"""

    def __init__(self):
        super().__init__()
        self.promofull_parser = XmlDataFrameConverter(
            list_key="Sales",
            id_field="PromotionID",
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
