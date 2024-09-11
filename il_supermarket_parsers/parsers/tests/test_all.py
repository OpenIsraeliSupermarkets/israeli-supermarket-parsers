from il_supermarket_parsers.parser_factroy import ParserFactory
from il_supermarket_scarper.scrappers_factory import ScraperFactory
from il_supermarket_parsers.parsers.tests.test_case import make_test_case


class BareketTestCase(make_test_case(ScraperFactory.BAREKET, ParserFactory.BAREKET, 5)):
    pass
