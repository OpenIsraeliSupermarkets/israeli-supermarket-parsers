from il_supermarket_parsers.documents import (
    XmlDataFrameConverter,
)
from .big_id import BigIDFileConverter


class BigIdBranchesFileConverter(BigIDFileConverter):
    """ "
    converter to all stores with ID instead of id and
    'Branches' instead of "Stores"
    """

    def __init__(self, stores_parser=None, **kwarg):
        super().__init__(
            stores_parser=(
                stores_parser
                if stores_parser
                else XmlDataFrameConverter(
                    list_key="Branches",
                    id_field="StoreID",
                    roots=[],
                )
            ),
            **kwarg
        )
