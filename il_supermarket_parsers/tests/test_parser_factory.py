from il_supermarket_scarper.scrappers_factory import ScraperFactory
from il_supermarket_parsers.parser_factory import ParserFactory


def test_enum_are_aligned():
    """make sure that the enum are aligned"""
    assert len(ParserFactory) == len(ScraperFactory)
    assert sorted(ParserFactory.__members__.keys()) == sorted(
        ScraperFactory.__members__.keys()
    )
