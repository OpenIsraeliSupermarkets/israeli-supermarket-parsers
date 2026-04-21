from il_supermarket_scarper.scrappers_factory import ScraperFactory
from il_supermarket_parsers.parser_factory import ParserFactory


def test_enum_are_aligned():
    """Every scraper chain must have a matching ParserFactory member.

    ParserFactory may list additional parsers (e.g. a new file format) before
    the scraper package adds a dedicated ScraperFactory entry.
    """
    scraper_keys = set(ScraperFactory.__members__)
    parser_keys = set(ParserFactory.__members__)
    missing_parsers = scraper_keys - parser_keys
    assert (
        not missing_parsers
    ), f"ScraperFactory entries without ParserFactory: {sorted(missing_parsers)}"
