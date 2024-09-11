from il_supermarket_parsers.parser_factroy import ParserFactory
from il_supermarket_scarper.scrappers_factory import ScraperFactory
from il_supermarket_parsers.parsers.tests.test_case import make_test_case


# @pytest.mark.run(order=1)
class BareketTestCase(make_test_case(ScraperFactory.BAREKET,  ParserFactory.BAREKET)):
    pass


# @pytest.mark.run(order=2)
class YaynotBitanTestCase(make_test_case(ScraperFactory.YAYNO_BITAN, ScraperFactory.YAYNO_BITAN)):
    pass


# @pytest.mark.run(order=3)
class CofixTestCase(make_test_case(ScraperFactory.COFIX, ScraperFactory.COFIX)):
    pass


# @pytest.mark.run(order=4)
class DorAlonTestCase(make_test_case(ScraperFactory.DOR_ALON, ScraperFactory.DOR_ALON)):
    pass


# @pytest.mark.run(order=5)
class GoodPharmTestCase(make_test_case(ScraperFactory.GOOD_PHARM, ScraperFactory.GOOD_PHARM)):
    pass


# @pytest.mark.run(order=6)
class HaziHinamTestCase(make_test_case(ScraperFactory.HAZI_HINAM, ScraperFactory.HAZI_HINAM)):
    pass


class HetCohen(make_test_case(ScraperFactory.HET_COHEN, ScraperFactory.HET_COHEN)):
    pass


# @pytest.mark.run(order=7)
class KeshetTestCase(make_test_case(ScraperFactory.KESHET, ScraperFactory.KESHET)):
    pass


# @pytest.mark.run(order=8)
class KingStoreTestCase(make_test_case(ScraperFactory.KING_STORE, ScraperFactory.KING_STORE)):
    pass


# @pytest.mark.run(order=9)
class Maayan2000TestCase(make_test_case(ScraperFactory.MAAYAN_2000, ScraperFactory.MAAYAN_2000)):
    pass


# @pytest.mark.run(order=10)
class MahsaniAShukTestCase(make_test_case(ScraperFactory.MAHSANI_ASHUK, ScraperFactory.MAHSANI_ASHUK)):
    pass


# @pytest.mark.run(order=12)
class MegaTestCase(make_test_case(ScraperFactory.MEGA, ScraperFactory.MEGA)):
    pass


# @pytest.mark.run(order=13)
class NetivHasefTestCase(make_test_case(ScraperFactory.NETIV_HASED, ScraperFactory.NETIV_HASED)):
    pass


# @pytest.mark.run(order=13)
class MeshnatYosef1TestCase(make_test_case(ScraperFactory.MESHMAT_YOSEF_1, ScraperFactory.MESHMAT_YOSEF_1)):
    pass


# @pytest.mark.run(order=13)
class MeshnatYosef2TestCase(make_test_case(ScraperFactory.MESHMAT_YOSEF_2, ScraperFactory.MESHMAT_YOSEF_2)):
    pass


# @pytest.mark.run(order=14)
class OsheradTestCase(make_test_case(ScraperFactory.OSHER_AD, ScraperFactory.OSHER_AD)):
    pass


# @pytest.mark.run(order=15)
class PolizerTestCase(make_test_case(ScraperFactory.POLIZER, ScraperFactory.POLIZER)):
    pass


# @pytest.mark.run(order=16)
class RamiLevyTestCase(make_test_case(ScraperFactory.RAMI_LEVY, ScraperFactory.RAMI_LEVY)):
    pass


# @pytest.mark.run(order=17)
class SalachDabachTestCase(make_test_case(ScraperFactory.SALACH_DABACH, ScraperFactory.SALACH_DABACH)):
    pass


# @pytest.mark.run(order=18)
class ShefaBarcartAshemTestCase(make_test_case(ScraperFactory.SHEFA_BARCART_ASHEM, ScraperFactory.SHEFA_BARCART_ASHEM)):
    pass


# @pytest.mark.run(order=19)
class ShufersalTestCase(make_test_case(ScraperFactory.SHUFERSAL, ScraperFactory.SHUFERSAL)):
    pass


# @pytest.mark.run(order=20)
class ShukAhirTestCase(make_test_case(ScraperFactory.SHUK_AHIR, ScraperFactory.SHUK_AHIR)):
    pass


# @pytest.mark.run(order=21)
class StopMarketTestCase(make_test_case(ScraperFactory.STOP_MARKET, ScraperFactory.STOP_MARKET)):
    pass


# @pytest.mark.run(order=22)
class SuperPharmTestCase(make_test_case(ScraperFactory.SUPER_PHARM, ScraperFactory.SUPER_PHARM)):
    pass


# @pytest.mark.run(order=23)
class SuperYudaTestCase(make_test_case(ScraperFactory.SUPER_YUDA, ScraperFactory.SUPER_YUDA)):
    pass


# @pytest.mark.run(order=30)
class SuperSapirTestCase(make_test_case(ScraperFactory.SUPER_SAPIR, ScraperFactory.SUPER_SAPIR)):
    pass


# @pytest.mark.run(order=24)
class FreshMarketAndSuperDoshTestCase(
    make_test_case(ScraperFactory.FRESH_MARKET_AND_SUPER_DOSH, ScraperFactory.FRESH_MARKET_AND_SUPER_DOSH)
):
    pass


# @pytest.mark.run(order=25)
class QuikTestCase(make_test_case(ScraperFactory.QUIK, ScraperFactory.QUIK)):
    pass


# @pytest.mark.run(order=25)
class TivTaamTestCase(make_test_case(ScraperFactory.TIV_TAAM, ScraperFactory.TIV_TAAM)):
    pass


# @pytest.mark.run(order=26)
class VictoryTestCase(make_test_case(ScraperFactory.VICTORY, ScraperFactory.VICTORY)):
    pass


# @pytest.mark.run(order=27)
class YellowTestCase(make_test_case(ScraperFactory.YELLOW, ScraperFactory.YELLOW)):
    pass


# @pytest.mark.run(order=28)
class YohananofTestCase(make_test_case(ScraperFactory.YOHANANOF, ScraperFactory.YOHANANOF)):
    pass


# @pytest.mark.run(order=29)
class ZolVeBegadolTestCase(make_test_case(ScraperFactory.ZOL_VEBEGADOL, ScraperFactory.ZOL_VEBEGADOL)):
    pass