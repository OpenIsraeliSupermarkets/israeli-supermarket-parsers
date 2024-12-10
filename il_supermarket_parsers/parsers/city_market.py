from il_supermarket_parsers.engines.base import BaseFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    ConditionalXmlDataFrameConverter,
)


class CityMarketGivatayim(BaseFileConverter):
    """
    File converter for Dor Alon supermarket chain.
    Extends: CofixFileConverter
    """


class CityMarketKiryatGat(BaseFileConverter):
    """
    File converter for Dor Alon supermarket chain.
    Extends: CofixFileConverter
    """


class CityMarketShops(BaseFileConverter):
    """
    File converter for Dor Alon supermarket chain.
    Extends: CofixFileConverter
    """

    def __init__(self):
        super().__init__(
            promofull_parser=ConditionalXmlDataFrameConverter(
                option_a=XmlDataFrameConverter(
                    list_key="Promotions",
                    id_field="PromotionId",
                    roots=["StoreId", "SubChainId", "ChainId"],
                    date_columns=["PromotionUpdateDate"],
                    ignore_column=["DllVerNo", "BikoretNo"],
                ),
                option_b=XmlDataFrameConverter(
                    list_key="Promotions",
                    id_field="PromotionId",
                    roots=[],
                    date_columns=["PromotionUpdateDate"],
                    ignore_column=["DllVerNo", "BikoretNo"],
                ),
                root_value="Root",
            ),
            stores_parser=SubRootedXmlDataFrameConverter(
                list_key="SubChainsXMLObject",
                sub_roots=["SubChainId", "SubChainName"],
                id_field="StoreId",
                list_sub_key="Store",
                roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
                last_mile=["Stores", "SubChainStoresXMLObject"],
            ),
        )
