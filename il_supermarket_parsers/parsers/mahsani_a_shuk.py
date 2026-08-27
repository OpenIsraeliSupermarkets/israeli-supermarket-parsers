from il_supermarket_parsers.engines import BigIDFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
    ConditionalXmlDataFrameConverter,
)

_ROW_ROOTS = ["ChainID", "SubChainID", "StoreID", "BikoretNo"]


def _promo_converter(list_key):
    """promo/promofull converter for a given row wrapper"""
    return XmlDataFrameConverter(
        list_key=list_key,
        id_field="PromotionID",
        roots=_ROW_ROOTS,
        date_columns=["PromotionUpdateTime"],
    )


def _promo_parser():
    """<Promotions> is what the new source publishes; <Sales> is the BigID legacy default."""
    return ConditionalXmlDataFrameConverter(
        option_a=_promo_converter("Promotions"),
        option_b=_promo_converter("Sales"),
        check_key="Promotions",
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
                roots=_ROW_ROOTS,
            ),
            pricefull_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=_ROW_ROOTS,
            ),
            promo_parser=_promo_parser(),
            promofull_parser=_promo_parser(),
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
