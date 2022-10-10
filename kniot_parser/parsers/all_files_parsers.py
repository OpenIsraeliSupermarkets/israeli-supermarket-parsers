from abc import ABC
from .documents_parsers import XmlDataFrameConverter, SubRootedXmlDataFrameConverter


class AllTypesFileConverter(ABC):
    """abstract parser"""

    def __init__(self, pricefull, promofull, stores, promo, price) -> None:
        self.pricefull = pricefull
        self.promofull = promofull
        self.stores = stores
        self.promo = promo
        self.price = price

    def get(self, file_type):
        """get parser by file type"""
        return getattr(self, file_type)



class DefualtFileConverter(AllTypesFileConverter):
    """the defualt converter"""

    def __init__(self):
        super().__init__(
            pricefull=XmlDataFrameConverter(
                full_data_snapshot=True,
                list_key="Items",
                id_field=["ItemCode","PriceUpdateDate"],
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            price=XmlDataFrameConverter(
                list_key="Items",
                id_field=["ItemCode","PriceUpdateDate"],
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            promo=XmlDataFrameConverter(
                list_key="Promotions",
                id_field=["PromotionId","PromotionUpdateDate"],
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
            ),
            promofull=XmlDataFrameConverter(
                full_data_snapshot=True,
                list_key="Promotions",
                id_field=["PromotionId","PromotionUpdateDate"],
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
            ),
            stores=SubRootedXmlDataFrameConverter(
                full_data_snapshot=True,
                list_key="SubChains",
                sub_roots=["SubChainId", "SubChainName"],
                id_field="StoreId",
                list_sub_key="Stores",
                roots=["ChainId", "ChainName", "LastUpdateDate", "LastUpdateTime"],
            ),
        )


class BigIDFileConverter(DefualtFileConverter):
    """a converter to all documents with ID instead of Id"""

    def __init__(self):
        super().__init__()
        self.pricefull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Products",
            id_field=["ItemCode","PriceUpdateDate"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
        )
        self.price = XmlDataFrameConverter(
            list_key="Products",
            id_field=["ItemCode","PriceUpdateDate"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
        )
        self.promo = XmlDataFrameConverter(
            list_key="Sales",
            id_field=["ItemCode","PriceUpdateDate"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
        self.promofull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Sales",
            id_field=["ItemCode","PromotionUpdateDate"],
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )


class BranchesFileConverter(BigIDFileConverter):
    """ "
    converter to all stores with ID instead of id and
    'Branches' instead of "Stores"
    """

    def __init__(self):
        super().__init__()
        self.stores = XmlDataFrameConverter(
            full_data_snapshot=True, list_key="Branches", id_field="StoreID", roots=[]
        )


class DetailsFileConverter(BigIDFileConverter):
    """ for super-pharam """
    def __init__(self):
        super().__init__()

        self.promofull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Header/Details",
            id_field=["PromotionId","PriceUpdateDate","ItemCode"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
        self.promo = XmlDataFrameConverter(
            list_key="Header/Details",
            id_field=["PromotionId","PriceUpdateDate","ItemCode"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )

        self.pricefull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Header/Details",
            id_field=["ItemCode","PriceUpdateDate"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
        self.price = XmlDataFrameConverter(
            list_key="Header/Details",
            id_field=["ItemCode","PriceUpdateDate"],
            roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
        )
