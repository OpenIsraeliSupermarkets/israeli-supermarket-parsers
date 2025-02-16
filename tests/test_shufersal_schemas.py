from il_supermarket_parsers.models.shufersal.shufersal_schema import (
    ShufersalPromo,
    ShufersalPrice,
    ShufersalStore,
)
from il_supermarket_parsers.models.shufersal.examples import (
    SINGLE_PRICE_FULL_EXAMPLE,
    SINGLE_PROMO_FULL_EXAMPLE,
    STORES_EXAMPLE_JSON,
)


def test_stores_schema_matches_example():
    ShufersalStoreData.model_validate(STORES_EXAMPLE_JSON)


def test_single_price_full_schema_matches_example():
    ShufersalPriceFullData.model_validate(SINGLE_PRICE_FULL_EXAMPLE)


def test_single_promo_full_schema_matches_example():
    ShufersalPromoFullData.model_validate(SINGLE_PROMO_FULL_EXAMPLE)
