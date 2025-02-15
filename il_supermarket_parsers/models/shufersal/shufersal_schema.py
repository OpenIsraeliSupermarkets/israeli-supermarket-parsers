from pydantic import BaseModel

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
