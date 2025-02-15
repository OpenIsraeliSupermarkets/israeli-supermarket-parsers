from pydantic import BaseModel, Field
from typing import List, Union


class ShufersalItem(BaseModel):
    item_code: str = Field(..., alias="ItemCode")
    item_name: str = Field(..., alias="ItemName")
    item_price: float = Field(..., alias="ItemPrice")
    item_unit: str = Field(..., alias="ItemUnit")
    manufacturer_name: str = Field(..., alias="ManufacturerName")
    manufacturer_item_description: str = Field(..., alias="ManufacturerItemDescription")


class ShufersalPromotion(BaseModel):
    promotion_id: str = Field(..., alias="PromotionId")
    promotion_description: str = Field(..., alias="PromotionDescription")
    promotion_start_date: str = Field(..., alias="PromotionStartDate")
    promotion_end_date: str = Field(..., alias="PromotionEndDate")
    reward_type: str = Field(..., alias="RewardType")


class ShufersalStore(BaseModel):
    store_id: str = Field(..., alias="StoreId")
    store_name: str = Field(..., alias="StoreName")
    store_address: str = Field(..., alias="StoreAddress")
    store_city: str = Field(..., alias="StoreCity")
    store_type: str = Field(..., alias="StoreType")


class ShufersalSubChain(BaseModel):
    sub_chain_id: str = Field(..., alias="SubChainId")
    sub_chain_name: str = Field(..., alias="SubChainName")
    stores: List[ShufersalStore] = Field(..., alias="Stores")


class ShufersalPriceFullData(BaseModel):
    chain_id: str = Field(..., alias="ChainId")
    sub_chain_id: str = Field(..., alias="SubChainId")
    store_id: str = Field(..., alias="StoreId")
    bikoret_no: str = Field(..., alias="BikoretNo")
    items: List[ShufersalItem] = Field(..., alias="Items")


class ShufersalPromoFullData(BaseModel):
    chain_id: str = Field(..., alias="ChainId")
    sub_chain_id: str = Field(..., alias="SubChainId")
    store_id: str = Field(..., alias="StoreId")
    bikoret_no: str = Field(..., alias="BikoretNo")
    promotions: List[ShufersalPromotion] = Field(..., alias="Promotions")


class ShufersalStoreData(BaseModel):
    chain_id: str = Field(..., alias="ChainId")
    chain_name: str = Field(..., alias="ChainName")
    last_update_date: str = Field(..., alias="LastUpdateDate")
    last_update_time: str = Field(..., alias="LastUpdateTime")
    sub_chains: List[ShufersalSubChain] = Field(..., alias="SubChains")


# Import example from examples.py
from .examples import STORES_EXAMPLE as SHUFERSAL_DATA_EXAMPLE
