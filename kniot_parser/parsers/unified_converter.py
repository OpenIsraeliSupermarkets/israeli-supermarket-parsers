from .all_files_parsers import (
    BranchesFileConverter,
    DefualtFileConverter,
    BigIDFileConverter,
)
from kniot_parser.utils import Logger


class UnifiedConverter(object):
    """
    unified converter across all types and sources
    """

    parsers = {
        "bareket": BranchesFileConverter,
        "mahsani a shuk": BigIDFileConverter,
        "Victory": BigIDFileConverter,
    }
    defult_parser = DefualtFileConverter

    def __init__(self, store_name, file_type) -> None:
        self.file_type_parser = (
            self.parsers[store_name]()
            if store_name in self.parsers
            else self.defult_parser()
        ).get(file_type)

        self.store_name = store_name

    def should_convert_to_incremental(self):
        """should we convert this file to incremenal to save storage"""
        return self.file_type_parser.is_full_data_snapshot()

    def get_key_column(self):
        """the key check document is index base on"""
        return self.file_type_parser.get_id()

    def convert(self, file):
        """convert a file base on the type,chain"""
        Logger.info(f" converting file {file}.")
        data_frame = self.file_type_parser.convert(file)

        Logger.info(f"file {file}, dataframe shape is {data_frame.shape}")
        data_frame = self.drop_duplicate(data_frame)

        Logger.info(f"file {file}, after duplicate drop, dataframe shape is {data_frame.shape}")
        return data_frame

    def drop_duplicate(self,data_frame):
        unique_rows = data_frame.astype('str').drop_duplicates().index

        if not unique_rows.empty:
            return data_frame.iloc[unique_rows,:]
        return data_frame