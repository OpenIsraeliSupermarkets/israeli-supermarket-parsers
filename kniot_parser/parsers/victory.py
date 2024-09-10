from kniot_parser.engines import BigIdBranchesFileConverter
from kniot_parser.documents import XmlDataFrameConverter


class VictoryFileConverter(BigIdBranchesFileConverter):
    def __init__(self):
        super().__init__()
        self.promofull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Sales",
            id_field=["ItemCode", "PromotionID"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
