from il_supermarket_parsers.engines.base import BaseFileConverter
from .bareket import BareketFileConverter
from .city_market import CityMarketGivatayim, CityMarketKiryatGat, CityMarketShops
from .confix import CofixFileConverter
from .hazi_hinam import HaziHinamFileConverter
from .mahsani_a_shuk import MahsaniAShukPromoFileConverter, MahsaniAShukNewFileConverter
from .meshant_yosef import MeshmatYosef1FileConverter, MeshmatYosef2FileConverter
from .salach_dabach import SalachDabachFileConverter
from .shufersal import ShufersalFileConverter
from .super_pharm import SuperPharmFileConverter
from .victory import VictoryFileConverter, VictoryNewFileConverter
from .het_cohen import HetChoenFileConverter, HetCohenNewFileConverter
from .tiv_taam import TivTaamFileConverter
from .other import *
