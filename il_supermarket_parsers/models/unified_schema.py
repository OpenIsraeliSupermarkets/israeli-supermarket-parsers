from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union


class SchemaField(BaseModel):
    description: str
    length: Optional[Union[int, str]]
    type: Literal["numeric", "alphanumeric", "date", "time"]
    name: str
    include: bool = True


class UnifiedStoreSchema(BaseModel):
    store_number: str
    store_type: str
    chain_name: str
    store_name: str
    city: str
    postal_code: str
    last_update_date: str
    last_update_time: str
    last_updated: str


class UnifiedItemPriceSchema(BaseModel):
    chain_code: str
    sub_chain_code: str
    store_number: str
    check_digit: Optional[str] = None
    price_update_time: Optional[str] = None
    product_barcode: Optional[str] = None
    internal_barcode: str
    product_name: str
    manufacturer_or_importer_name: str
    country_of_origin: str
    product_description: str
    product_quantity_measure: str
    product_quantity: str
    unit_of_measure: str
    items_per_package: str
    total_price: Optional[str] = None
    unit_price: Optional[str] = None
    currency: str


class UnifiedPromoSchema(BaseModel):
    chain_code: str
    sub_chain_code: str
    store_number: str
    check_digit: str
    promo_update_time: str
    product_barcode: Optional[str] = None
    internal_barcode: str
    promo_code: str
    multiple_promos: str
    promo_id: str
    promo_description: str
    promo_start_date: str
    promo_start_time: str
    promo_end_date: str
    promo_end_time: str
    target_population: str
    minimum_quantity_for_promo: str
    purchase_limit_in_promo: str
    discount_rate: str
    minimum_purchase_amount: str
    total_promo_price: Optional[str] = None
    unit_price_after_promo: str
    minimum_promo_items_in_store: str
    additional_promo_restrictions: str
    additional_promo_text: str
    discount_type: str
    valid_until: str


class UnifiedSchema(BaseModel):
    stores: List[UnifiedStoreSchema]
    prices: List[UnifiedItemPriceSchema]
    promotions: List[UnifiedPromoSchema]

    @classmethod
    def from_json_file(cls, json_path: str) -> "UnifiedSchema":
        """Load schema from JSON file"""
        import json

        with open(json_path, "r") as f:
            data = json.load(f)
            return cls(**data)
