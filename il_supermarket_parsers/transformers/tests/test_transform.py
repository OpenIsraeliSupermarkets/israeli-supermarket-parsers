from il_supermarket_parsers.models.shufersal.shufersal_schema import (
    ShufersalStore,
)
from il_supermarket_parsers.models.shufersal.examples import (
    STORES_EXAMPLE_JSON,
)
from il_supermarket_parsers.transformers.transform import ShufersalMapper


from il_supermarket_parsers.models.unified_schema import (
    UnifiedStoreSchema,
)


class TestShufersalTransformations:
    def test_shufersal_mapper_store_data_to_unified_schema_successful(self):
        source_data = STORES_EXAMPLE_JSON
        destination_data = ShufersalMapper.map_store_data_to_unified_schema(
            ShufersalStore,
            UnifiedStoreSchema,
            source_data,
        )
