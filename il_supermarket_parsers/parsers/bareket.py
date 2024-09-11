from il_supermarket_parsers.engines import BigIdBranchesFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class BareketFileConverter(BigIdBranchesFileConverter):

    def __init__(self):
        super().__init__(
            promofull_parser=XmlDataFrameConverter(
                list_key="Sales",
                id_field=["PromotionID", "ItemCode"],
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PriceUpdateDate"],
            ),
            stores_parser=XmlDataFrameConverter(
                list_key="Branches",
                id_field="StoreID",
                roots=[],
                ChainName="ברקת",
            ),
        )
