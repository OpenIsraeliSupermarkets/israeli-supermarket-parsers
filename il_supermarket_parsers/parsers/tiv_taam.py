from il_supermarket_parsers.engines import BigIdBranchesFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    ConditionalXmlDataFrameConverter,
)


class TivTaamFileConverter(BigIdBranchesFileConverter):
    """טיב טעם"""

    def __init__(self):
        super().__init__(
            promo_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["DllVerNo"],
            ),
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["DllVerNo"],
            ),
            stores_parser=SubRootedXmlDataFrameConverter(
                list_key="SubChains",
                list_sub_key="Stores",
                sub_roots=["SubChainId", "SubChainName"],
                id_field="StoreId",
                roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                ignore_column=["XmlDocVersion"],
            ),
            price_parser=ConditionalXmlDataFrameConverter(
                option_a=XmlDataFrameConverter(
                    list_key="Items",
                    id_field="ItemCode",
                    roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                    ignore_column=["DllVerNo"],
                ),
                option_b=XmlDataFrameConverter(
                    list_key="NewDataSet",
                    id_field="ItemCode",
                    filter_element="item",
                    roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                    ignore_column=["DllVerNo", "schema"],
                ),
                check_key="Items",
            ),
            pricefull_parser=ConditionalXmlDataFrameConverter(
                option_a=XmlDataFrameConverter(
                    list_key="Items",
                    id_field="ItemCode",
                    roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                    ignore_column=["DllVerNo"],
                ),
                option_b=XmlDataFrameConverter(
                    list_key="NewDataSet",
                    id_field="ItemCode",
                    filter_element="item",
                    roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                    ignore_column=["DllVerNo", "schema"],
                ),
                check_key="Items",
            ),
        )
