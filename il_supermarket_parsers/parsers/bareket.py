from il_supermarket_parsers.engines import BigIdBranchesFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
)


class BareketFileConverter(BigIdBranchesFileConverter):
    """Barket converter"""

    def __init__(self):
        super().__init__(
            stores_parser=SubRootedXmlDataFrameConverter(
                id_field="StoreId",
                list_key="SubChains",
                roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                list_sub_key="Stores",
                sub_roots=["SubChainName", "SubChainId"],
            ),
            price_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            pricefull_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            promo_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
        )
