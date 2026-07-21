from il_supermarket_parsers.engines import BaseFileConverter
from il_supermarket_parsers.documents import (
    ConditionalXmlDataFrameConverter,
    SubRootedXmlDataFrameConverter,
    SubRootedXmlOptions,
    XmlDataFrameConverter,
)


class ShufersalFileConverter(BaseFileConverter):
    """שופרסל"""

    def __init__(self) -> None:
        legacy_stores_parser = XmlDataFrameConverter(
            list_key="STORES",
            id_field="STOREID",
            roots=["CHAINID", "LASTUPDATEDATE"],
        )
        subchain_stores_parser = SubRootedXmlDataFrameConverter(
            list_key="SubChains",
            id_field="StoreID",
            options=SubRootedXmlOptions(
                roots=[
                    "ChainID",
                    "ChainName",
                    "LastUpdateDate",
                    "LastUpdateTime",
                ],
                list_sub_key="Stores",
                sub_roots=["SubChainID", "SubChainName"],
            ),
        )
        super().__init__(
            stores_parser=ConditionalXmlDataFrameConverter(
                option_a=subchain_stores_parser,
                option_b=legacy_stores_parser,
                check_key="SubChains",
            )
        )
