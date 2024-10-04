from il_supermarket_parsers.engines import BaseFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class SalachDabachFileConverter(BaseFileConverter):
    """סאלח דאבח"""

    def __init__(self) -> None:
        super().__init__(
            price_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["DllVerNo", "XmlDocVersion"],
            ),
            pricefull_parser=XmlDataFrameConverter(
                list_key="Items",
                id_field="ItemId",
                roots=["ChainId", "SubChainId", "StoreId", "BikoretNo"],
                ignore_column=["DllVerNo", "XmlDocVersion"],
            ),
        )
