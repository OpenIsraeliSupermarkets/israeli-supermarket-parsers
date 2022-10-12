from .all_files_parsers import (
    BranchesFileConverter,
    DefualtFileConverter,
    BigIDFileConverter,
    DetailsFileConverter,
    ShufersalFileConverter,
    CofixFileConverter,
    BranchesPromoFileConverter
)
from kniot_parser.utils import Logger


class UnifiedConverter(object):
    """
    unified converter across all types and sources
    """

    parsers = {
        "bareket": BranchesFileConverter,
        "mahsani a shuk": BranchesPromoFileConverter,
        "Victory": BranchesFileConverter,
        "Super-Pharm":DetailsFileConverter,
        "Shufersal":ShufersalFileConverter,
        "cofix":CofixFileConverter
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

        data_frame = self.drop_duplicate_missing_inforamtion(data_frame)

        return data_frame

    def drop_duplicate(self,data_frame):
        """ drop duplicate entries in the database"""
        unique_rows = data_frame.astype('str').drop_duplicates().index

        if not unique_rows.empty:
            Logger.info(f"Droping {data_frame.shape[0]-unique_rows.shape[0]} duplicate entries.")
            return data_frame.iloc[unique_rows,:]
        return data_frame

    def drop_duplicate_missing_inforamtion(self,data_frame):

        def group_function(data):
            if data.shape[0] == 1:
                return data.head(1)
            elif data.shape[0] == 2:
                change = data.loc[:,~(data.iloc[0] == data.iloc[1]).values]
                if change.shape[1] == 1 and 'UnitQty' in change.columns and change['UnitQty'].iloc[0] == 'Unknown ':
                    return data.tail(1)
                else:
                    raise ValueError(f"Change of {change} is not detected.")
            else:
                raise ValueError("Don't support duplicate for more the 2 rows.")
            
        if not data_frame.empty:
            if (data_frame[self.file_type_parser.get_id()].value_counts() > 1).any():
                return data_frame.groupby(self.file_type_parser.get_id()).apply(group_function).reset_index(drop=True)

        return data_frame
