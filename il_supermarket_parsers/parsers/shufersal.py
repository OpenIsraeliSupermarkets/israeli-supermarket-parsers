from il_supermarket_parsers.engines import BaseFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class ShufersalFileConverter(BaseFileConverter):
    """שופרסל"""

    def __init__(self) -> None:
        super().__init__(
            stores_parser=XmlDataFrameConverter(
                list_key="STORES",
                id_field="STOREID",
                roots=["CHAINID", "LASTUPDATEDATE"],
            )
        )
