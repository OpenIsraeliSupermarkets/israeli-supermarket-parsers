from il_supermarket_parsers.engines import BaseFileConverter
from il_supermarket_parsers.documents import SubRootedXmlDataFrameConverter


class MeshmatYosef1FileConverter(BaseFileConverter):
    """
    File converter for Hazi Hinam supermarket chain.
    """

    def __init__(self) -> None:
        super().__init__(
            stores_parser=SubRootedXmlDataFrameConverter(
                id_field="StoreID",
                list_key="SubChains",
                roots=["ChainID", "ChainName", "LastUpdateDate", "LastUpdateTime"],
                list_sub_key="Stores",
                sub_roots=["SubChainName", "SubChainID"],
                ignore_column=["XmlDocVersion"],
            )
        )


class MeshmatYosef2FileConverter(BaseFileConverter):
    """
    File converter for Meshmat Yosef 2 supermarket chain.
    Extends: BaseFileConverter
    """
