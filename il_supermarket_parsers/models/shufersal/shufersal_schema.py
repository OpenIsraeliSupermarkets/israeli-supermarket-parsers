from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import List

# TODO: create model for common fields (ChainId, SubChainId, StoreId, BikoretNo)
class ShufersalStore(BaseModel):
    ChainId: str
    ChainName: str
    SubChainId: str
    SubChainName: str
    StoreId: str
    StoreName: str
    StoreAddress: str
    StoreCity: str
    StoreType: str
    LastUpdateDate: str


class Item(BaseModel):
    itemcode: str
    itemtype: str
    isgiftitem: str


class AdditionalInfo(BaseModel):
    additionaliscoupon: Optional[str] = None
    additionalgiftcount: Optional[str] = None
    additionalistotal: Optional[str] = None
    additionalisactive: Optional[str] = None

class ShufersalPromo(BaseModel):
    ChainId: str
    SubChainId: str
    StoreId: str
    BikoretNo: str
    PromotionId: str
    PromotionDescription: str
    PromotionStartDate: str
    PromotionEndDate: str
    PromotionStartHour: str
    PromotionEndHour: str
    RewardType: str
    DiscountType: str
    DiscountRate: Optional[float]
    DiscountedPricePerMida: Optional[float]
    MinQty: Optional[float]
    MaxQty: Optional[float]
    MinPurchaseAmnt: Optional[float]
    MinNoOfItemOfered: Optional[int]
    AdditionalRestrictions: Optional[str]
    Remark: Optional[str]
    IsWeightedPromo: Optional[bool]
    AllowMultipleDiscounts: Optional[bool]


class ShufersalPrice(BaseModel):
    ChainId: str
    SubChainId: str
    StoreId: str
    BikoretNo: str
    ItemCode: str
    ItemName: str
    ItemPrice: float
    ItemUnit: str
    ManufacturerName: str
    ManufacturerItemDescription: str
