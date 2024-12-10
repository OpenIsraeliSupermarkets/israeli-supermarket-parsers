from il_supermarket_parsers.engines.base import BaseFileConverter
from .confix import CofixFileConverter
from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    ConditionalXmlDataFrameConverter,
)


class YaynoBitanFileConverter(BaseFileConverter):
    """
    File converter for Yayno Bitan supermarket chain.
    Extends: BaseFileConverter
    """


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


class HaziHinamFileConverter(CofixFileConverter):
    """
    File converter for Hazi Hinam supermarket chain.
    Extends: CofixFileConverter
    """


class KeshetFileConverter(BaseFileConverter):
    """
    File converter for Keshet supermarket chain.
    Extends: BaseFileConverter
    """


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


class MeshmatYosef1FileConverter(BaseFileConverter):
    """
    File converter for Meshmat Yosef 1 supermarket chain.
    Extends: BaseFileConverter
    """


class MeshmatYosef2FileConverter(BaseFileConverter):
    """
    File converter for Meshmat Yosef 2 supermarket chain.
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


class ZolVebegadolFileConverter(BaseFileConverter):
    """
    File converter for Zol Vebegadol supermarket chain.
    Extends: BaseFileConverter
    """


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
                try_parser=XmlDataFrameConverter(
                    list_key="Promotions",
                    id_field="PromotionId",
                    roots=["StoreId", "SubChainId", "ChainId"],
                    date_columns=["PromotionUpdateDate"],
                    ignore_column=["DllVerNo", "BikoretNo"],
                ),
                catch_parser=XmlDataFrameConverter(
                    list_key="Promotions",
                    id_field="PromotionId",
                    roots=[],
                    date_columns=["PromotionUpdateDate"],
                    ignore_column=["DllVerNo", "BikoretNo"],
                ),
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
