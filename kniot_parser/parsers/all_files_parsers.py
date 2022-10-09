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

    # def get_id(self, file_type):
    #     """get"""
    #     return self.converter_by_type(file_type).get_id()

    # def convert(self, file_type, full_path):
    #     """ convert file to data frame """
    #     results = self.converter_by_type(file_type).convert(full_path)

    #     if results.shape[0] == 0:
    #         raise ValueError(f" file {full_path} failed to be pharse.")
    #     return results

    # def should_convert_to_incremental(self, file_type):
    #     """ check if should be converted to incremental """
    #     return self.converter_by_type(file_type).is_full_data_snapshot()


class DefualtFileConverter(AllTypesFileConverter):
    """the defualt converter"""

    def __init__(self):
        super().__init__(
            pricefull=XmlDataFrameConverter(
                full_data_snapshot=True,
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            price=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
            ),
            promo=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                date_columns=["PromotionUpdateDate"],
            ),
            promofull=XmlDataFrameConverter(
                full_data_snapshot=True,
                list_key="Promotions",
                id_field="PromotionId",
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
            id_field="ItemCode",
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
        )
        self.price = XmlDataFrameConverter(
            list_key="Products",
            id_field="ItemCode",
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
        )
        self.promo = XmlDataFrameConverter(
            list_key="Sales",
            id_field="ItemCode",
            roots=["ChainID", "SubChainID", "StoreID", "BikoretNo"],
            date_columns=["PriceUpdateDate"],
        )
        self.promofull = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="Sales",
            id_field="ItemCode",
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
