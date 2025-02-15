def main():

    from il_supermarket_parsers.models.shufersal.examples import PRICE_FULL_EXAMPLE

    from il_supermarket_parsers.transformers.transform import map_model
    from il_supermarket_parsers.models.unified_schema import UnifiedPriceFullSchema
    from il_supermarket_parsers.models.shufersal.shufersal_schema import (
        ShufersalPriceFullData,
    )

    model_b = map_model(
        ShufersalPriceFullData, UnifiedPriceFullSchema, PRICE_FULL_EXAMPLE
    )
    print(model_b)


if __name__ == "__main__":
    main()
