from il_supermarket_parsers.engines import BigIdBranchesFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class BareketFileConverter(BigIdBranchesFileConverter):
    
    def __init__(self):
        super().__init__()
        self.promofull_parser = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Sales",
            id_field=["PromotionID", "ItemCode"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
        self.stores_parser = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Branches",
            id_field="StoreID",
            roots=[],
            ChainName="ברקת",
        )
