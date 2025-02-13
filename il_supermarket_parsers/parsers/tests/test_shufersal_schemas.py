from il_supermarket_parsers.models.shufersal.shufersal_schema import (
    ShufersalPriceData,
    ShufersalPromoData,
    ShufersalStoreData,
)
from il_supermarket_parsers.models.shufersal.examples import (
    PRICE_FULL_EXAMPLE,
    PROMO_FULL_EXAMPLE,
    STORES_EXAMPLE,
    PRICE_UPDATE_EXAMPLE,
    PROMO_UPDATE_EXAMPLE,
)


def test_price_full_schema():
    ShufersalPriceData.model_validate(PRICE_FULL_EXAMPLE)


def test_price_update_schema():
    ShufersalPriceData.model_validate(PRICE_UPDATE_EXAMPLE)


def test_promo_full_schema():
    ShufersalPromoData.model_validate(PROMO_FULL_EXAMPLE)


def test_promo_update_schema():
    ShufersalPromoData.model_validate(PROMO_UPDATE_EXAMPLE)


def test_stores_schema():
    ShufersalStoreData.model_validate(STORES_EXAMPLE)
