from kniot_parser.engines import BigIdBranchesFileConverter
from kniot_parser.documents import XmlDataFrameConverter


class BareketFileConverter(BigIdBranchesFileConverter):
    def __init__(self):
        super().__init__()
        self.promofull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Sales",
            id_field=["PromotionID", "ItemCode"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
        self.stores = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Branches",
            id_field="StoreID",
            roots=[],
            ChainName="ברקת",
        )
