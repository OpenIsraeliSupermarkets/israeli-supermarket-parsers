from kniot_parser.engines import BigIDFileConverter
from kniot_parser.documents import XmlDataFrameConverter


class MahsaniAShukPromoFileConverter(BigIDFileConverter):
    """ "
    converter to all stores with ID instead of id and
    'Branches' instead of "Stores"
    """

    def __init__(self):
        super().__init__()
        self.stores = XmlDataFrameConverter(
            full_data_snapshot=True, list_key="Branches", id_field="StoreID", roots=[]
        )
        self.promo = XmlDataFrameConverter(
            list_key="Sales",
            id_field=[
                "ItemCode",
                "PriceUpdateDate",
                "ClubID",
                "ItemType",
                "RewardType",
                "PromotionID",
            ],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
        self.promofull = XmlDataFrameConverter(
            list_key="Sales",
            id_field=[
                "ItemCode",
                "PriceUpdateDate",
                "ClubID",
                "ItemType",
                "RewardType",
                "PromotionID",
            ],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
