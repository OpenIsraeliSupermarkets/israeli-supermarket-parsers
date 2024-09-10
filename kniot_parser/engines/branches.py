from kniot_parser.documents import (
    XmlDataFrameConverter,
)
from .base import BigIDFileConverter


class BigIdBranchesFileConverter(BigIDFileConverter):
    """ "
    converter to all stores with ID instead of id and
    'Branches' instead of "Stores"
    """

    def __init__(self):
        super().__init__()
        self.stores = XmlDataFrameConverter(
            full_data_snapshot=True, list_key="Branches", id_field="StoreID", roots=[]
        )
