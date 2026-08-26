from il_supermarket_parsers.engines import BigIDFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
    ConditionalXmlDataFrameConverter,
)

_PRICE_ROOTS = ["ChainId", "SubChainId", "StoreId", "BikoretNo"]


def _price_converter(list_key):
    """price/pricefull converter for a given row wrapper"""
    return XmlDataFrameConverter(
        list_key=list_key,
        id_field="ItemCode",
        roots=_PRICE_ROOTS,
    )


def _promo_converter(list_key):
    """promo/promofull converter for a given row wrapper"""
    return XmlDataFrameConverter(
        list_key=list_key,
        id_field="PromotionId",
        roots=_PRICE_ROOTS,
    )


def _price_parser():
    """Super-Pharm migrated price files to <Items>; older dumps still use <Details>."""
    return ConditionalXmlDataFrameConverter(
        option_a=_price_converter("Items"),
        option_b=_price_converter("Details"),
        check_key="Items",
    )


def _promo_parser():
    """Super-Pharm promo files may ship as <Promotions> or legacy <Details>."""
    return ConditionalXmlDataFrameConverter(
        option_a=_promo_converter("Promotions"),
        option_b=_promo_converter("Details"),
        check_key="Promotions",
    )


class SuperPharmFileConverter(BigIDFileConverter):
    """סופר פארם"""

    def __init__(self):
        super().__init__(
            promofull_parser=_promo_parser(),
            promo_parser=_promo_parser(),
            pricefull_parser=_price_parser(),
            price_parser=_price_parser(),
            stores_parser=SubRootedXmlDataFrameConverter(
                list_key="SubChains",
                id_field="StoreID",
                options=SubRootedXmlOptions(
                    list_sub_key="Stores",
                    sub_roots=["SubChainID", "SubChainName"],
                    roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                ),
            ),
        )
