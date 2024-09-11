from il_supermarket_parsers.utils import Logger
from abc import ABC


class DataFrameNormlizer(ABC):
    """
    converting dataframe to a normlize form
    """

    def __init__(self) -> None:
        pass

    def normlize(self, file, data_frame, row_limit=None):
        pass
