from il_supermarket_parsers.models.shufersal.shufersal_schema import (
    ShufersalPromo,
    ShufersalStore,
    ShufersalPrice,
)
from il_supermarket_parsers.models.shufersal.examples import (
    SINGLE_ITEM_PRICE_EXAMPLE,
    SINGLE_PROMO_FULL_EXAMPLE,
    STORES_EXAMPLE_JSON,
)
from il_supermarket_parsers.transformers.transform import ShufersalMapper


from il_supermarket_parsers.models.unified_schema import (
    UnifiedItemPriceSchema,
    UnifiedPromoSchema,
    UnifiedStoreSchema,
)


class TestShufersalTransformations:
    # TODO: separate responsibility of tests (load example, test schema, test transform)
    def test_shufersal_mapper_store_data_to_unified_schema_successful(self):
        source_data = STORES_EXAMPLE_JSON
        destination_data = ShufersalMapper.map_store_data_to_unified_schema(
            ShufersalStore,
            UnifiedStoreSchema,
            source_data,
        )

    def test_shufersal_map_single_promo_to_unified_schema_successful(self):
        source_data = SINGLE_PROMO_FULL_EXAMPLE
        destination_data = ShufersalMapper.map_promo_data_to_unified_schema(
            ShufersalPromo,
            UnifiedPromoSchema,
            source_data,
        )

    def test_shufersal_map_single_price_to_unified_schema_successful(self):
        source_data = SINGLE_ITEM_PRICE_EXAMPLE
        destination_data = ShufersalMapper.map_price_data_to_unified_schema(
            ShufersalPrice,
            UnifiedItemPriceSchema,
            source_data,
        )
