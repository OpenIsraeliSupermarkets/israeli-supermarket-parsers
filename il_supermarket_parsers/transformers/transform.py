from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from typing import Dict, Type
from pydantic import BaseModel
from typing import Type, TypeVar

from il_supermarket_parsers.models.unified_schema import (
    UnifiedStoreSchema,
)
from il_supermarket_parsers.models.shufersal.shufersal_schema import (
    ShufersalStore,
)

T = TypeVar("T", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)


def map_model(source_cls: Type[T], destination_cls: Type[U], data: dict) -> U:
    data = source_cls.model_validate(data).model_dump()
    return destination_cls.model_validate(data)


class ShufersalMapper:
    @staticmethod
    def map_store_data_to_unified_schema(
        source: Type[ShufersalStore],
        destination: Type[UnifiedStoreSchema],
        data: dict,
    ) -> UnifiedStoreSchema:
        source_data = source.model_validate(data)
        return UnifiedStoreSchema(
            store_number=source_data.StoreId,
            store_type=source_data.StoreType,
            chain_name=source_data.ChainName,
            store_name=source_data.StoreName,
            city=source_data.StoreCity,
            postal_code=source_data.StoreAddress,
            last_update_date=source_data.LastUpdateDate,
            last_update_time="",  # Assuming no equivalent field in ShufersalStore
            last_updated=source_data.LastUpdateDate,
        )
