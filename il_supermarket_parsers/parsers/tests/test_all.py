from il_supermarket_scarper.scrappers_factory import ScraperFactory
from il_supermarket_parsers.parser_factory import ParserFactory
from il_supermarket_parsers.parsers.tests.test_case import make_test_case


class BareketTestCase(make_test_case(ScraperFactory.BAREKET, ParserFactory.BAREKET)):
    """
    Test case for Bareket supermarket.
    """


class YaynotBitanTestCase(
    make_test_case(ScraperFactory.YAYNO_BITAN, ParserFactory.YAYNO_BITAN)
):
    """
    Test case for Yaynot Bitan supermarket.
    """


class CofixTestCase(make_test_case(ScraperFactory.COFIX, ParserFactory.COFIX)):
    """
    Test case for Cofix supermarket.
    """


class DorAlonTestCase(make_test_case(ScraperFactory.DOR_ALON, ParserFactory.DOR_ALON)):
    """
    Test case for Dor Alon supermarket.
    """


class GoodPharmTestCase(
    make_test_case(ScraperFactory.GOOD_PHARM, ParserFactory.GOOD_PHARM)
):
    """
    Test case for Good Pharm supermarket.
    """


class HaziHinamTestCase(
    make_test_case(ScraperFactory.HAZI_HINAM, ParserFactory.HAZI_HINAM)
):
    """
    Test case for Hazi Hinam supermarket.
    """


class HetCohenTestCase(
    make_test_case(ScraperFactory.HET_COHEN, ParserFactory.HET_COHEN)
):
    """
    Test case for Het Cohen supermarket.
    """


class KeshetTestCase(make_test_case(ScraperFactory.KESHET, ParserFactory.KESHET)):
    """
    Test case for Keshet supermarket.
    """


class KingStoreTestCase(
    make_test_case(ScraperFactory.KING_STORE, ParserFactory.KING_STORE)
):
    """
    Test case for King Store supermarket.
    """


class Maayan2000TestCase(
    make_test_case(ScraperFactory.MAAYAN_2000, ParserFactory.MAAYAN_2000)
):
    """
    Test case for Maayan 2000 supermarket.
    """


class MahsaniAShukTestCase(
    make_test_case(ScraperFactory.MAHSANI_ASHUK, ParserFactory.MAHSANI_ASHUK)
):
    """
    Test case for Mahsani AShuk supermarket.
    """


class MegaTestCase(make_test_case(ScraperFactory.MEGA, ParserFactory.MEGA)):
    """
    Test case for Mega supermarket.
    """


class NetivHasefTestCase(
    make_test_case(ScraperFactory.NETIV_HASED, ParserFactory.NETIV_HASED)
):
    """
    Test case for Netiv Hased supermarket.
    """


class MeshnatYosef1TestCase(
    make_test_case(ScraperFactory.MESHMAT_YOSEF_1, ParserFactory.MESHMAT_YOSEF_1)
):
    """
    Test case for Meshnat Yosef 1 supermarket.
    """


class MeshnatYosef2TestCase(
    make_test_case(ScraperFactory.MESHMAT_YOSEF_2, ParserFactory.MESHMAT_YOSEF_2)
):
    """
    Test case for Meshnat Yosef 2 supermarket.
    """


class OsheradTestCase(make_test_case(ScraperFactory.OSHER_AD, ParserFactory.OSHER_AD)):
    """
    Test case for Osher Ad supermarket.
    """


class PolizerTestCase(make_test_case(ScraperFactory.POLIZER, ParserFactory.POLIZER)):
    """
    Test case for Polizer supermarket.
    """


class RamiLevyTestCase(
    make_test_case(ScraperFactory.RAMI_LEVY, ParserFactory.RAMI_LEVY)
):
    """
    Test case for Rami Levy supermarket.
    """


class SalachDabachTestCase(
    make_test_case(ScraperFactory.SALACH_DABACH, ParserFactory.SALACH_DABACH)
):
    """
    Test case for Salach Dabach supermarket.
    """


class ShefaBarcartAshemTestCase(
    make_test_case(
        ScraperFactory.SHEFA_BARCART_ASHEM, ParserFactory.SHEFA_BARCART_ASHEM
    )
):
    """
    Test case for Shefa Barcart Ashem supermarket.
    """


class ShufersalTestCase(
    make_test_case(ScraperFactory.SHUFERSAL, ParserFactory.SHUFERSAL)
):
    """
    Test case for Shufersal supermarket.
    """


class ShukAhirTestCase(
    make_test_case(ScraperFactory.SHUK_AHIR, ParserFactory.SHUK_AHIR)
):
    """
    Test case for Shuk Ahir supermarket.
    """


class StopMarketTestCase(
    make_test_case(ScraperFactory.STOP_MARKET, ParserFactory.STOP_MARKET)
):
    """
    Test case for Stop Market supermarket.
    """


class SuperPharmTestCase(
    make_test_case(ScraperFactory.SUPER_PHARM, ParserFactory.SUPER_PHARM)
):
    """
    Test case for Super Pharm supermarket.
    """


class SuperYudaTestCase(
    make_test_case(ScraperFactory.SUPER_YUDA, ParserFactory.SUPER_YUDA)
):
    """
    Test case for Super Yuda supermarket.
    """


class SuperSapirTestCase(
    make_test_case(ScraperFactory.SUPER_SAPIR, ParserFactory.SUPER_SAPIR)
):
    """
    Test case for Super Sapir supermarket.
    """


class FreshMarketAndSuperDoshTestCase(
    make_test_case(
        ScraperFactory.FRESH_MARKET_AND_SUPER_DOSH,
        ParserFactory.FRESH_MARKET_AND_SUPER_DOSH,
    )
):
    """
    Test case for Fresh Market and Super Dosh supermarket.
    """


class QuikTestCase(make_test_case(ScraperFactory.QUIK, ParserFactory.QUIK)):
    """
    Test case for Quik supermarket.
    """


class TivTaamTestCase(make_test_case(ScraperFactory.TIV_TAAM, ParserFactory.TIV_TAAM)):
    """
    Test case for Tiv Taam supermarket.
    """


class VictoryTestCase(make_test_case(ScraperFactory.VICTORY, ParserFactory.VICTORY)):
    """
    Test case for Victory supermarket.
    """


class YellowTestCase(make_test_case(ScraperFactory.YELLOW, ParserFactory.YELLOW)):
    """
    Test case for Yellow convenience store.
    """


class YohananofTestCase(
    make_test_case(ScraperFactory.YOHANANOF, ParserFactory.YOHANANOF)
):
    """
    Test case for Yohananof supermarket.
    """


class ZolVeBegadolTestCase(
    make_test_case(ScraperFactory.ZOL_VEBEGADOL, ParserFactory.ZOL_VEBEGADOL)
):
    """
    Test case for Zol VeBegadol supermarket.
    """
