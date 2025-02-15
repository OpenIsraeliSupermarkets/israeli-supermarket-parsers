from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from typing import Dict, Type
from pydantic import BaseModel
from il_supermarket_parsers.models.shufersal.shufersal_schema import (
    ShufersalPriceFullData,
    ShufersalPromoFullData,
    ShufersalStoreData,
)
from il_supermarket_parsers.models.unified_schema import (
    UnifiedPriceFullFileSchema,
    UnifiedPromoFullFileSchema,
    UnifiedStoreFileSchema,
    UniformSchema,
)
from il_supermarket_parsers.config.config import ConfigMapping, get_config_mapping


class TransformerFactory:
    def __init__(self):
        self.transformers = {
            (ShufersalPriceFullData, UnifiedPriceFullFileSchema): get_config_mapping(
                ConfigMapping.PRICE_FULL_FILE
            ),
            (ShufersalPromoFullData, UnifiedPromoFullFileSchema): get_config_mapping(
                ConfigMapping.PROMO_FULL_FILE
            ),
            (ShufersalStoreData, UnifiedStoreFileSchema): get_config_mapping(
                ConfigMapping.STORE_FILE
            ),
        }


from typing import Type, TypeVar

T = TypeVar("T", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)


def map_model(source_cls: Type[T], destination_cls: Type[U], data: dict) -> U:
    data = source_cls.model_validate(data).model_dump()
    return destination_cls.model_validate(data)
# Example usage
from il_supermarket_parsers.models.shufersal.examples import PRICE_FULL_EXAMPLE

model_a = ShufersalPriceFullData.model_validate(PRICE_FULL_EXAMPLE)
model_b = map_model(model_a, UnifiedPriceFullFileSchema)
print(model_b)
