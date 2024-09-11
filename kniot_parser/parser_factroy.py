import random
import os
from enum import Enum
import kniot_parser.parsers as all_parsers


class ParserFactory(Enum):
    """all parsers avaliabe"""

    BAREKET = all_parsers.Bareket
    YAYNO_BITAN = all_parsers.YaynotBitan
    COFIX = all_parsers.Cofix
    DOR_ALON = all_parsers.DorAlon
    GOOD_PHARM = all_parsers.GoodPharm
    HAZI_HINAM = all_parsers.HaziHinam
    HET_COHEN = all_parsers.HetCohen
    KESHET = all_parsers.Keshet
    KING_STORE = all_parsers.KingStore
    MAAYAN_2000 = all_parsers.Maayan2000
    MAHSANI_ASHUK = all_parsers.MahsaniAShuk
    MEGA = all_parsers.Mega
    NETIV_HASED = all_parsers.NetivHased
    MESHMAT_YOSEF_1 = all_parsers.MeshnatYosef1
    MESHMAT_YOSEF_2 = all_parsers.MeshnatYosef2
    OSHER_AD = all_parsers.Osherad
    POLIZER = all_parsers.Polizer
    RAMI_LEVY = all_parsers.RamiLevy
    SALACH_DABACH = all_parsers.SalachDabach
    SHEFA_BARCART_ASHEM = all_parsers.ShefaBarcartAshem
    SHUFERSAL = all_parsers.Shufersal
    SHUK_AHIR = all_parsers.ShukAhir
    STOP_MARKET = all_parsers.StopMarket
    SUPER_PHARM = all_parsers.SuperPharm
    SUPER_YUDA = all_parsers.SuperYuda
    SUPER_SAPIR = all_parsers.SuperSapir
    FRESH_MARKET_AND_SUPER_DOSH = all_parsers.FreshMarketAndSuperDosh
    QUIK = all_parsers.Quik
    TIV_TAAM = all_parsers.TivTaam
    VICTORY = all_parsers.Victory
    YELLOW = all_parsers.Yellow
    YOHANANOF = all_parsers.Yohananof
    ZOL_VEBEGADOL = all_parsers.ZolVeBegadol

    @classmethod
    def all_listed_parsers(cls):
        """get all the scarpers and filter disabled scrapers"""
        return list(cls)

    @classmethod
    def all_active(cls):
        """get all the scarpers and filter disabled scrapers"""
        return (member for member in cls if cls.is_scraper_enabled(member))

    @classmethod
    def sample(cls, n=1):
        """sample n from the parsers"""
        return random.sample(cls.all_parsers_name(), n)

    @classmethod
    def all_parsers(cls):
        """list all parsers possible to use"""
        return [e.value for e in ParserFactory.all_active()]

    @classmethod
    def all_parsers_name(cls):
        """get the class name of all listed parsers"""
        return [e.name for e in ParserFactory.all_active()]

    @classmethod
    def get(cls, class_name):
        """get a parsers by class name"""
        enum = None
        if isinstance(class_name, ParserFactory):
            enum = class_name
        elif class_name in cls.all_scrapers_name():
            enum = getattr(ParserFactory, class_name)
        else:
            raise ValueError(f"class_names {class_name} not found")
        if not cls.is_scraper_enabled(enum):
            return None
        return enum.value
