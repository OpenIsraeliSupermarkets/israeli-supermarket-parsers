from il_supermarket_parsers.models.shufersal import (
    PRICE_FULL_EXAMPLE,
    PROMO_FULL_EXAMPLE,
    STORES_EXAMPLE,
    ShufersalPriceFullData,
    ShufersalPromoFullData,
    ShufersalStoreData,
)

from il_supermarket_parsers.transformers.transform import map_model


from il_supermarket_parsers.models.unified_schema import (
    UnifiedPriceFullSchema,
    UnifiedPromoFullSchema,
    UnifiedStoreSchema,
)

class TestShufersalTransformations:
    def test_price_transformation(self):
        source_data = PRICE_FULL_EXAMPLE
        transformed_data = map_model(ShufersalPriceFullData, UnifiedPriceFullSchema, source_data)
        assert transformed_data.dict() == source_data

    def test_promo_transformation(self):
        source_data = PROMO_FULL_EXAMPLE
        transformed_data = map_model(ShufersalPromoFullData, UnifiedPromoFullSchema, source_data)
        assert transformed_data.dict() == source_data

    def test_store_transformation(self):
        source_data = STORES_EXAMPLE
        transformed_data = map_model(ShufersalStoreData, UnifiedStoreSchema, source_data)
        assert transformed_data.dict() == source_data
