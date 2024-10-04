from il_supermarket_parsers.engines import BigIDFileConverter
from il_supermarket_parsers.documents import XmlDataFrameConverter


class MahsaniAShukPromoFileConverter(BigIDFileConverter):
    """ "
    Majsani A Shuk converter
    """

    def __init__(self):
        super().__init__(
            stores_parser=XmlDataFrameConverter(
                list_key="Branches",
                id_field="StoreID",
                roots=[],
            )
        )
