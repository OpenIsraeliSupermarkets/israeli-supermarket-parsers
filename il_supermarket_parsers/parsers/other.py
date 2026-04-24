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
                ignore_column=[
                    "XmlDocVersion",
                    "DllVerNo",
                    "remark",
                    "Remark",
                    "Remarks",
                ],
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
                    "Remarks",
                    "Remark",
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
                    "Remarks",
                    "Remark",
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
                    "Remarks",
                    "Remark",
                ],
            ),
        )


class QuikFileConverter(BaseFileConverter):
    """
    File converter for Quik supermarket chain.
    Extends: BaseFileConverter
    """


class YellowFileConverter(BaseFileConverter):
    """
    File converter for Yellow supermarket chain.
    Extends: BaseFileConverter
    """


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
                    "Remarks",
                    "Remark",
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
