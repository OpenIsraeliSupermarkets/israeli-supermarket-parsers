from il_supermarket_parsers.engines import BigIDFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
    ConditionalXmlDataFrameConverter,
)

_ROW_ROOTS = ["ChainId", "SubChainId", "StoreId", "BikoretNo"]
_STORE_ROOTS = ["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"]


def _price_converter(list_key):
    """price/pricefull converter for a given row wrapper"""
    return XmlDataFrameConverter(
        list_key=list_key,
        id_field="ItemCode",
        roots=_ROW_ROOTS,
    )


def _promo_converter(list_key):
    """promo/promofull converter for a given row wrapper"""
    return XmlDataFrameConverter(
        list_key=list_key,
        id_field="PromotionId",
        roots=_ROW_ROOTS,
    )


def _first_present(build_converter, list_keys):
    """Chain converters so the first wrapper present in the file is the one used.

    The final key is the fallback and is applied without a check, so a file whose
    wrapper matches none of the candidates still goes through the historical
    converter rather than yielding zero rows.
    """
    *candidates, fallback = list_keys
    parser = build_converter(fallback)
    for list_key in reversed(candidates):
        parser = ConditionalXmlDataFrameConverter(
            option_a=build_converter(list_key),
            option_b=parser,
            check_key=list_key,
        )
    return parser


def _price_parser():
    """<Items> is the shape Super-Pharm publishes now; older dumps used <Details>."""
    return _first_present(_price_converter, ["Items", "Products", "Details"])


def _promo_parser():
    """<Promotions> is the standard shape; older dumps used <Details>."""
    return _first_present(_promo_converter, ["Promotions", "Sales", "Details"])


def _stores_parser():
    """Super-Pharm nests stores under <SubChains>; flat <Stores> dumps stay readable."""
    return ConditionalXmlDataFrameConverter(
        option_a=SubRootedXmlDataFrameConverter(
            list_key="SubChains",
            id_field="StoreID",
            options=SubRootedXmlOptions(
                list_sub_key="Stores",
                sub_roots=["SubChainID", "SubChainName"],
                roots=_STORE_ROOTS,
            ),
        ),
        option_b=XmlDataFrameConverter(
            list_key="Stores",
            id_field="StoreID",
            roots=_STORE_ROOTS,
        ),
        check_key="SubChains",
    )


class SuperPharmFileConverter(BigIDFileConverter):
    """סופר פארם"""

    def __init__(self):
        super().__init__(
            promofull_parser=_promo_parser(),
            promo_parser=_promo_parser(),
            pricefull_parser=_price_parser(),
            price_parser=_price_parser(),
            stores_parser=_stores_parser(),
        )
