from il_supermarket_parsers.engines import BigIdBranchesFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class TivTaamFileConverter(BigIdBranchesFileConverter):
    """ טיב טעם"""
    def __init__(self):
        super().__init__(
            promofull_parser=XmlDataFrameConverter(
                list_key="Sales",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PriceUpdateDate"],
            ),
            stores_parser=XmlDataFrameConverter(
                list_key="SubChains",
                id_field="StoreId",
                roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
            ),
        )
