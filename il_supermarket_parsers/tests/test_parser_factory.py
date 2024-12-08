from il_supermarket_parsers.parser_factory import ParserFactory
from il_supermarket_scarper.scrappers_factory import ScraperFactory


def test_enum_are_aligned():
    assert len(ParserFactory) == len(ScraperFactory)
    assert sorted(ParserFactory.__members__.keys()) == sorted(
        ScraperFactory.__members__.keys()
    )
