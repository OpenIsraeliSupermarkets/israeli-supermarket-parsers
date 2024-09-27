import random

import il_supermarket_parsers.parsers as all_parsers
from il_supermarket_parsers.utils import DuplicateValueEnum


class ParserFactory(DuplicateValueEnum):
    """all parsers avaliabe"""

    BAREKET = all_parsers.BareketFileConverter
    YAYNO_BITAN = all_parsers.BaseFileConverter
    COFIX = all_parsers.CofixFileConverter
    DOR_ALON = all_parsers.CofixFileConverter
    GOOD_PHARM = all_parsers.CofixFileConverter
    HAZI_HINAM = all_parsers.CofixFileConverter
    HET_COHEN = all_parsers.HetChoenFileConverter
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
    FRESH_MARKET_AND_SUPER_DOSH = all_parsers.CofixFileConverter
    QUIK = all_parsers.BaseFileConverter
    TIV_TAAM = all_parsers.TivTaamFileConverter
    VICTORY = all_parsers.VictoryFileConverter
    YELLOW = all_parsers.BaseFileConverter
    YOHANANOF = all_parsers.BaseFileConverter
    ZOL_VEBEGADOL = all_parsers.BaseFileConverter

    @classmethod
    def all_listed_parsers(cls):
        """get all the scarpers and filter disabled scrapers"""
        return list(cls)

    @classmethod
    def sample(cls, n=1):
        """sample n from the parsers"""
        return random.sample(cls.all_parsers_name(), n)

    @classmethod
    def all_parsers(cls):
        """list all parsers possible to use"""
        return list(ParserFactory._members.values())

    @classmethod
    def all_parsers_name(cls):
        """get the class name of all listed parsers"""
        return list(ParserFactory._members.keys())

    @classmethod
    def get(cls, key):
        """get a parsers by class name"""
        value = None
        if isinstance(key, str) and key in ParserFactory._members:
            value = ParserFactory._members[key]
            name = key
        elif key in ParserFactory._members.values():
            value = key
            name = list(filter(lambda x: x[1] == key, ParserFactory._members.items()))[
                0
            ][0]
        else:
            raise ValueError(f"class_names {key} not found")
        return name, value
