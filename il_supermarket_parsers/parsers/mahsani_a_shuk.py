from il_supermarket_parsers.engines import BigIDFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
)


class MahsaniAShukPromoFileConverter(BigIDFileConverter):
    """ "
    Majsani A Shuk converter
    """

    def __init__(self):
        super().__init__(
            stores_parser=XmlDataFrameConverter(
                list_key="Branches",
                id_field="StoreID",
                roots=[],
            )
        )


class MahsaniAShukNewFileConverter(BigIDFileConverter):
    """Mahsani A Shuk - new source"""

    def __init__(self):
        super().__init__(
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
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionID",
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                date_columns=["PromotionUpdateTime"],
            ),
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
                    list_sub_key="Stores",
                    sub_roots=["SubChainId", "SubChainName"],
                    ignore_column=[],
                ),
            ),
        )
