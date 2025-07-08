from il_supermarket_parsers.engines import BigIDFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
)


class SuperPharmFileConverter(BigIDFileConverter):
    """סופר פארם"""

    def __init__(self):
        super().__init__(
            promofull_parser=XmlDataFrameConverter(
                list_key="Details",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            promo_parser=XmlDataFrameConverter(
                list_key="Details",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            pricefull_parser=XmlDataFrameConverter(
                list_key="Details",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            price_parser=XmlDataFrameConverter(
                list_key="Details",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            stores_parser=SubRootedXmlDataFrameConverter(
                list_key="SubChains",
                id_field="StoreID",
                list_sub_key="Stores",
                sub_roots=["SubChainID", "SubChainName"],
                roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
            ),
        )
