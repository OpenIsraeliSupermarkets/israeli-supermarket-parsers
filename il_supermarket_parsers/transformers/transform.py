from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Type
from pydantic import BaseModel
from typing import Type, TypeVar

from il_supermarket_parsers.models.unified_schema import (
    UnifiedStoreSchema,
    UnifiedPromoFullSchema,
    UnifiedPriceFullSchema,
)
from il_supermarket_parsers.models.shufersal.shufersal_schema import (
    ShufersalPromo,
    ShufersalStore,
    ShufersalPrice,
)

T = TypeVar("T", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)


def map_model(source_cls: Type[T], destination_cls: Type[U], data: dict) -> U:
    data = source_cls.model_validate(data).model_dump()
    return destination_cls.model_validate(data)


class Mapper(ABC):
    pass


class ShufersalMapper(Mapper):
    @staticmethod
    def map_store_data_to_unified_schema(
        source: Type[ShufersalStore],
        destination: Type[UnifiedStoreSchema],
        data: dict,
    ) -> UnifiedStoreSchema:
        source_data = source.model_validate(data)
        return destination(
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

    @staticmethod
    def map_promo_data_to_unified_schema(
        source: Type[ShufersalPromo],
        destination: Type[UnifiedPromoFullSchema],
        data: dict,
    ) -> UnifiedPromoFullSchema:
        source_data: ShufersalPromo = source.model_validate(data)

        return destination(
            chain_code=source_data.ChainId,
            sub_chain_code=source_data.SubChainId,
            store_number=source_data.StoreId,
            check_digit=source_data.BikoretNo,
            promo_update_time=source_data.PromotionStartDate,
            product_barcode=source_data.PromotionId,
            internal_barcode=source_data.PromotionId,
            promo_code=source_data.PromotionId,
            multiple_promos=str(source_data.AllowMultipleDiscounts),
            promo_id=source_data.PromotionId,
            promo_description=source_data.PromotionDescription,
            promo_start_date=source_data.PromotionStartDate,
            promo_start_time=source_data.PromotionStartHour,
            promo_end_date=source_data.PromotionEndDate,
            promo_end_time=source_data.PromotionEndHour,
            target_population=str(source_data.IsWeightedPromo),
            minimum_quantity_for_promo=str(source_data.MinQty),
            purchase_limit_in_promo=str(source_data.MaxQty),
            discount_rate=str(source_data.DiscountRate),
            minimum_purchase_amount=str(source_data.MinPurchaseAmnt),
            unit_price_after_promo=str(source_data.DiscountedPricePerMida),
            minimum_promo_items_in_store=str(source_data.MinNoOfItemOfered),
            additional_promo_restrictions=str(source_data.AdditionalRestrictions),
            additional_promo_text=str(source_data.Remark),
            discount_type=str(source_data.DiscountType),
            valid_until=source_data.PromotionEndDate,
        )

    @staticmethod
    def map_price_data_to_unified_schema(
        source: Type[ShufersalPrice],
        destination: Type[UnifiedPriceFullSchema],
        data: dict,
    ) -> UnifiedPriceFullSchema:
        source_data: ShufersalPrice = source.model_validate(data)
        return destination(
            chain_code=source_data.ChainId,
            sub_chain_code=source_data.SubChainId,
            store_number=source_data.StoreId,
            check_digit=source_data.BikoretNo,
            product_barcode=source_data.ItemCode,
            internal_barcode=source_data.ItemCode,
            product_name=source_data.ItemName,
            manufacturer_or_importer_name=source_data.ManufacturerName,
            country_of_origin=source_data.ManufacturerItemDescription,
            product_description=source_data.ItemUnit,
            product_quantity_measure=source_data.ItemUnit,
            product_quantity=str(source_data.ItemPrice),
            unit_of_measure=source_data.ItemUnit,
            items_per_package=source_data.ItemUnit,
            currency="NIS",
        )
