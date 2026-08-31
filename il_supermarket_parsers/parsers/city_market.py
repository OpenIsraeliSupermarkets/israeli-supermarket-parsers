from il_supermarket_parsers.engines.base import BaseFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
    ConditionalXmlDataFrameConverter,
)


class CityMarketGivatayim(BaseFileConverter):
    """
    File converter for City Market Givatayim (deprecated / closed).
    """


class CityMarketKiryatOno(BaseFileConverter):
    """
    File converter for City Market Kiryat Ono (deprecated / closed).
    """


class CityMarketKiryatGat(BaseFileConverter):
    """
    File converter for City Market Kiryat Gat.
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
                id_field="StoreId",
                options=SubRootedXmlOptions(
                    sub_roots=["SubChainId", "SubChainName"],
                    list_sub_key="Store",
                    roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                    ignore_column=["XmlDocVersion", "DllVerNo"],
                    last_mile=["Stores", "SubChainStoresXMLObject"],
                ),
            ),
        )
