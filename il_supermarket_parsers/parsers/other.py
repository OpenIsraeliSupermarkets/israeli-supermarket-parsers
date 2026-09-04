from il_supermarket_parsers.engines.base import BaseFileConverter
from il_supermarket_parsers.documents import (
    ConditionalXmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
    XmlDataFrameConverter,
)

from .confix import CofixFileConverter


class YaynoBitanFileConverter(BaseFileConverter):
    """
    File converter for Yayno Bitan supermarket chain.
    Extends: BaseFileConverter
    """

    def __init__(self) -> None:
        super().__init__(
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
        )


class DorAlonFileConverter(CofixFileConverter):
    """
    File converter for Dor Alon supermarket chain.
    Extends: CofixFileConverter
    """


class GoodPharmFileConverter(CofixFileConverter):
    """
    File converter for Good Pharm supermarket chain.
    Extends: CofixFileConverter
    """


class KeshetFileConverter(BaseFileConverter):
    """
    File converter for Keshet supermarket chain.
    Extends: BaseFileConverter
    """

    def __init__(self) -> None:
        super().__init__(
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
        )


class KingStoreFileConverter(BaseFileConverter):
    """
    File converter for King Store supermarket chain.
    Extends: BaseFileConverter
    """


class Maayan2000FileConverter(BaseFileConverter):
    """
    File converter for Maayan 2000 supermarket chain.
    Extends: BaseFileConverter
    """


class MegaFileConverter(BaseFileConverter):
    """
    File converter for Mega supermarket chain.
    Extends: BaseFileConverter
    """


class NetivHasedFileConverter(BaseFileConverter):
    """
    File converter for Netiv Hased supermarket chain.
    Extends: BaseFileConverter
    """


class OsherAdFileConverter(BaseFileConverter):
    """
    File converter for Osher Ad supermarket chain.
    Extends: BaseFileConverter
    """


class PolizerFileConverter(BaseFileConverter):
    """
    File converter for Polizer supermarket chain.
    Extends: BaseFileConverter
    """


class RamiLevyFileConverter(BaseFileConverter):
    """
    File converter for Rami Levy supermarket chain.
    Extends: BaseFileConverter
    """

    def __init__(self) -> None:
        super().__init__(
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
                ignore_column=[
                    "XmlDocVersion",
                    "DllVerNo",
                ],
            ),
        )


class ShefaBarcartAshemFileConverter(BaseFileConverter):
    """
    File converter for Shefa Barcart Ashem supermarket chain.
    Extends: BaseFileConverter
    """


class ShukAhirFileConverter(BaseFileConverter):
    """
    File converter for Shuk Ahir supermarket chain.
    Extends: BaseFileConverter
    """


class StopMarketFileConverter(BaseFileConverter):
    """
    File converter for Stop Market supermarket chain.
    Extends: BaseFileConverter
    """


class SuperYudaFileConverter(BaseFileConverter):
    """
    File converter for Super Yuda supermarket chain.
    Extends: BaseFileConverter
    """

    def __init__(self) -> None:
        super().__init__(
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
                ignore_column=[
                    "XmlDocVersion",
                    "DllVerNo",
                ],
            ),
        )


class SuperSapirFileConverter(BaseFileConverter):
    """
    File converter for Super Sapir supermarket chain.
    Extends: BaseFileConverter
    """


class FreshMarketAndSuperDoshFileConverter(CofixFileConverter):
    """
    File converter for Fresh Market and Super Dosh supermarket chains.
    Extends: CofixFileConverter
    """

    def __init__(self) -> None:
        super().__init__(
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=[
                    "XmlDocVersion",
                    "DllVerNo",
                ],
            ),
        )


class QuikFileConverter(BaseFileConverter):
    """
    File converter for Quik supermarket chain.
    Extends: BaseFileConverter
    """


_YELLOW_ROW_ROOTS = ["ChainId", "SubChainId", "StoreId", "BikoretNo"]
_YELLOW_IGNORE = ["XmlDocVersion", "DllVerNo"]


def _yellow_price_converter(list_key):
    """price/pricefull converter for a given row wrapper"""
    return XmlDataFrameConverter(
        list_key=list_key,
        id_field="ItemCode",
        roots=_YELLOW_ROW_ROOTS,
        ignore_column=_YELLOW_IGNORE,
    )


def _yellow_promo_converter(list_key):
    """promo/promofull converter for a given row wrapper"""
    return XmlDataFrameConverter(
        list_key=list_key,
        id_field="PromotionId",
        roots=_YELLOW_ROW_ROOTS,
        date_columns=["PromotionUpdateDate"],
        ignore_column=_YELLOW_IGNORE,
    )


def _yellow_first_present(build_converter, list_keys):
    """Use the first wrapper present in the file; last key is the legacy fallback."""
    *candidates, fallback = list_keys
    parser = build_converter(fallback)
    for list_key in reversed(candidates):
        parser = ConditionalXmlDataFrameConverter(
            option_a=build_converter(list_key),
            option_b=parser,
            check_key=list_key,
        )
    return parser


class YellowFileConverter(BaseFileConverter):
    """
    File converter for Yellow supermarket chain.
    Extends: BaseFileConverter
    """

    def __init__(self) -> None:
        super().__init__(
            price_parser=_yellow_first_present(
                _yellow_price_converter, ["Items", "Products", "Details"]
            ),
            pricefull_parser=_yellow_first_present(
                _yellow_price_converter, ["Items", "Products", "Details"]
            ),
            promo_parser=_yellow_first_present(
                _yellow_promo_converter, ["Promotions", "Sales", "Details"]
            ),
            promofull_parser=_yellow_first_present(
                _yellow_promo_converter, ["Promotions", "Sales", "Details"]
            ),
        )


class YohananofFileConverter(BaseFileConverter):
    """
    File converter for Yohananof supermarket chain.
    Extends: BaseFileConverter
    """

    def __init__(self) -> None:
        super().__init__(
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
                ignore_column=[
                    "XmlDocVersion",
                    "DllVerNo",
                ],
            ),
        )


class ZolVebegadolFileConverter(BaseFileConverter):
    """
    File converter for Zol Vebegadol supermarket chain.
    Extends: BaseFileConverter
    """


class WoltFileConverter(BaseFileConverter):
    """
    wolt
    """

    def __init__(self) -> None:
        wolt_promo_with_items = SubRootedXmlDataFrameConverter(
            list_key="Promotions",
            id_field="ItemCode",
            options=SubRootedXmlOptions(
                roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
                list_sub_key="PromotionItems",
                sub_roots=[
                    "Remarks",
                    "AdditionalRestrictions",
                    "ClubId",
                    "PromotionEndHour",
                    "PromotionUpdateTime",
                    "PromotionId",
                    "PromotionDescription",
                    "PromotionStartDate",
                    "PromotionStartHour",
                    "PromotionEndDate",
                ],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
        )
        wolt_promo_empty_store = XmlDataFrameConverter(
            list_key="Promotions",
            id_field="ItemCode",
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            ignore_column=["XmlDocVersion", "DllVerNo"],
        )
        super().__init__(
            promofull_parser=ConditionalXmlDataFrameConverter(
                option_a=wolt_promo_with_items,
                option_b=wolt_promo_empty_store,
                check_key="Promotion",
            )
        )
