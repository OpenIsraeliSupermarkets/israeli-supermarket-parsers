from il_supermarket_parsers.engines import BigIDFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class MahsaniAShukPromoFileConverter(BigIDFileConverter):
    """ "
    converter to all stores with ID instead of id and
    'Branches' instead of "Stores"
    """

    def __init__(self):
        super().__init__(
            stores_parser=XmlDataFrameConverter(
                list_key="Branches",
                id_field="StoreID",
                roots=[],
            ),
            promo_parser=XmlDataFrameConverter(
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
            ),
            promofull_parser=XmlDataFrameConverter(
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
            ),
        )
