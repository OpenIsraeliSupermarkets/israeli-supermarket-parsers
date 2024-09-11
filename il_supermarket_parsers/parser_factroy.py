import random
import os
from enum import Enum
import il_supermarket_parsers.parsers as all_parsers


class ParserFactory(Enum):
    """all parsers avaliabe"""

    BAREKET = all_parsers.BareketFileConverter
    YAYNO_BITAN = all_parsers.BaseFileConverter
    COFIX = all_parsers.CofixFileConverter
    DOR_ALON = all_parsers.BaseFileConverter
    GOOD_PHARM = all_parsers.BaseFileConverter
    HAZI_HINAM = all_parsers.BaseFileConverter
    HET_COHEN = all_parsers.BaseFileConverter
    KESHET = all_parsers.BaseFileConverter
    KING_STORE = all_parsers.BaseFileConverter
    MAAYAN_2000 = all_parsers.BaseFileConverter
    MAHSANI_ASHUK = all_parsers.MahsaniAShukPromoFileConverter
    MEGA = all_parsers.BaseFileConverter
    NETIV_HASED = all_parsers.BaseFileConverter
    MESHMAT_YOSEF_1 = all_parsers.BaseFileConverter
    MESHMAT_YOSEF_2 = all_parsers.BaseFileConverter
    OSHER_AD = all_parsers.BaseFileConverter
    POLIZER = all_parsers.BaseFileConverter
    RAMI_LEVY = all_parsers.BaseFileConverter
    SALACH_DABACH = all_parsers.SalachDabachFileConverter
    SHEFA_BARCART_ASHEM = all_parsers.BaseFileConverter
    SHUFERSAL = all_parsers.ShufersalFileConverter
    SHUK_AHIR = all_parsers.BaseFileConverter
    STOP_MARKET = all_parsers.BaseFileConverter
    SUPER_PHARM = all_parsers.SuperPharmFileConverter
    SUPER_YUDA = all_parsers.BaseFileConverter
    SUPER_SAPIR = all_parsers.BaseFileConverter
    FRESH_MARKET_AND_SUPER_DOSH = all_parsers.BaseFileConverter
    QUIK = all_parsers.BaseFileConverter
    TIV_TAAM = all_parsers.BaseFileConverter
    VICTORY = all_parsers.VictoryFileConverter
    YELLOW = all_parsers.BaseFileConverter
    YOHANANOF = all_parsers.BaseFileConverter
    ZOL_VEBEGADOL = all_parsers.BaseFileConverter

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
