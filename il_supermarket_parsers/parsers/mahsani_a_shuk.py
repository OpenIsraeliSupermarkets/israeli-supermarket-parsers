from il_supermarket_parsers.engines import BigIDFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class MahsaniAShukPromoFileConverter(BigIDFileConverter):
    """ "
    converter to all stores with ID instead of id and
    'Branches' instead of "Stores"
    """

    def __init__(self):
        super().__init__(
            stores_parser=XmlDataFrameConverter(
                list_key="Branches",
                id_field="StoreID",
                roots=[],
            )
        )
