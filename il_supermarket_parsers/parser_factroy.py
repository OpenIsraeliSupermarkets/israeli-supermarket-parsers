import random
from enum import Enum
import il_supermarket_parsers.parsers as all_parsers


class ParserFactory(Enum):
    """all parsers avaliabe"""

    BAREKET = all_parsers.BareketFileConverter
    YAYNO_BITAN = all_parsers.YaynoBitanFileConverter
    COFIX = all_parsers.CofixFileConverter
    DOR_ALON = all_parsers.DorAlonFileConverter
    GOOD_PHARM = all_parsers.GoodPharmFileConverter
    HAZI_HINAM = all_parsers.HaziHinamFileConverter
    HET_COHEN = all_parsers.HetChoenFileConverter
    KESHET = all_parsers.KeshetFileConverter
    KING_STORE = all_parsers.KingStoreFileConverter
    MAAYAN_2000 = all_parsers.Maayan2000FileConverter
    MAHSANI_ASHUK = all_parsers.MahsaniAShukPromoFileConverter
    MEGA = all_parsers.MegaFileConverter
    NETIV_HASED = all_parsers.NetivHasedFileConverter
    MESHMAT_YOSEF_1 = all_parsers.MeshmatYosef1FileConverter
    MESHMAT_YOSEF_2 = all_parsers.MeshmatYosef2FileConverter
    OSHER_AD = all_parsers.OsherAdFileConverter
    POLIZER = all_parsers.PolizerFileConverter
    RAMI_LEVY = all_parsers.RamiLevyFileConverter
    SALACH_DABACH = all_parsers.SalachDabachFileConverter
    SHEFA_BARCART_ASHEM = all_parsers.ShefaBarcartAshemFileConverter
    SHUFERSAL = all_parsers.ShufersalFileConverter
    SHUK_AHIR = all_parsers.ShukAhirFileConverter
    STOP_MARKET = all_parsers.StopMarketFileConverter
    SUPER_PHARM = all_parsers.SuperPharmFileConverter
    SUPER_YUDA = all_parsers.SuperYudaFileConverter
    SUPER_SAPIR = all_parsers.SuperSapirFileConverter
    FRESH_MARKET_AND_SUPER_DOSH = all_parsers.FreshMarketAndSuperDoshFileConverter
    QUIK = all_parsers.QuikFileConverter
    TIV_TAAM = all_parsers.TivTaamFileConverter
    VICTORY = all_parsers.VictoryFileConverter
    YELLOW = all_parsers.YellowFileConverter
    YOHANANOF = all_parsers.YohananofFileConverter
    ZOL_VEBEGADOL = all_parsers.ZolVebegadolFileConverter

    @classmethod
    def all_listed_parsers(cls):
        """get all the scarpers and filter disabled scrapers"""
        return list(cls)

    @classmethod
    def sample(cls, n=1):
        """sample n from the parsers"""
        return random.sample(cls.all_parsers_name(), n)

    @classmethod
    def all_parsers_classes(cls):
        """list all parsers possible to use"""
        return [member.value for member in ParserFactory]

    @classmethod
    def all_parsers_name(cls):
        """get the class name of all listed parsers"""
        return [member.name for member in ParserFactory]

    @classmethod
    def get(cls, class_name):
        """get a parsers by class name"""
        enum = None
        if isinstance(class_name, ParserFactory):
            enum = class_name
        elif class_name in cls.all_parsers_name():
            enum = getattr(ParserFactory, class_name)

        if enum is None:
            raise ValueError(f"class_names {class_name} not found")
        return enum.value
