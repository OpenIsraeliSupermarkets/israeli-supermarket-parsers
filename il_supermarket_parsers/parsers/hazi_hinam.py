from il_supermarket_parsers.engines import BaseFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class HaziHinamFileConverter(BaseFileConverter):
    """
    File converter for Hazi Hinam supermarket chain.
    """

    def __init__(self) -> None:
        super().__init__(
            price_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
            pricefull_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemCode",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
            promo_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
            promofull_parser=XmlDataFrameConverter(
                list_key="Promotions",
                id_field="PromotionId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["XmlDocVersion", "DllVerNo"],
            ),
            stores_parser=XmlDataFrameConverter(
                id_field="StoreID",
                list_key="Stores",
                roots=["ChainId"],
                ignore_column=[],
            ),
        )
