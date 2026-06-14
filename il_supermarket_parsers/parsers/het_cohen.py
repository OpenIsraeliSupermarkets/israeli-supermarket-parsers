from il_supermarket_parsers.engines import BigIdBranchesFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
)


class HetChoenFileConverter(BigIdBranchesFileConverter):
    """het cohen converter"""

    def __init__(self):
        super().__init__(
            stores_parser=XmlDataFrameConverter(
                list_key="Branches",
                id_field="StoreID",
                roots=[],
            ),
            promo_parser=XmlDataFrameConverter(
                list_key="Sales",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PriceUpdateDate"],
            ),
            promofull_parser=XmlDataFrameConverter(
                list_key="Sales",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PriceUpdateDate"],
            ),
        )


class HetCohenNewFileConverter(BigIdBranchesFileConverter):
    """ח. כהן - new source (laibcatalog API)"""

    def __init__(self):
        super().__init__(
            stores_parser=SubRootedXmlDataFrameConverter(
                list_key="SubChains",
                id_field="StoreID",
                options=SubRootedXmlOptions(
                    roots=[
                        "ChainID",
                        "ChainName",
                        "LastUpdateDate",
                        "LastUpdateTime",
                    ],
                    sub_roots=["SubChainId", "SubChainName"],
                    list_sub_key="Stores",
                ),
            ),
            price_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            ),
            pricefull_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            ),
            promo_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PromotionUpdateTime"],
            ),
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PromotionUpdateTime"],
            ),
        )
