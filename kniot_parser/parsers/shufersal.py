from kniot_parser.engines import BaseFileConverter
from kniot_parser.documents import XmlDataFrameConverter


class ShufersalFileConverter(BaseFileConverter):
    def __init__(self) -> None:
        super().__init__()

        self.stores_parser = XmlDataFrameConverter(
            full_data_snapshot=True,
            list_key="STORES",
            id_field=["STOREID"],
            roots=["ChainId", "ChainName", "LASTUPDATEDATE"],
            renames={"LASTUPDATEDATE": "DocLASTUPDATEDATE"},
            chainid="7290027600007",
        )
