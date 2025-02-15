from il_supermarket_parsers.models.shufersal.shufersal_schema import (
    ShufersalPriceFullData,
    ShufersalPromoFullData,
    ShufersalStoreData,
)
from il_supermarket_parsers.models.shufersal.examples import (
    PRICE_FULL_EXAMPLE,
    PROMO_FULL_EXAMPLE,
    STORES_EXAMPLE,
)


def test_price_full_schema_matches_example():
    ShufersalPriceFullData.model_validate(PRICE_FULL_EXAMPLE)


def test_promo_full_schema_matches_example():
    ShufersalPromoFullData.model_validate(PROMO_FULL_EXAMPLE)


def test_stores_schema_matches_example():
    ShufersalStoreData.model_validate(STORES_EXAMPLE)
