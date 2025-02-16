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
    found_folder: str
    file_name: str
    chainid: str
    subchainid: str
    storeid: str
    bikoretno: str
    priceupdatedate: str
    itemcode: str
    itemtype: str
    itemname: str
    manufacturername: str
    manufacturecountry: Optional[str] = None
    manufactureritemdescription: str
    unitqty: Optional[str] = None
    quantity: float
    bisweighted: int
    unitofmeasure: str
    qtyinpackage: float
    itemprice: float
    unitofmeasureprice: float
    allowdiscount: int
    itemstatus: int


class ShufersalData(BaseModel):
    stores: List[ShufersalStore]
    prices: List[ShufersalPrice]
    promotions: List[ShufersalPromo]
