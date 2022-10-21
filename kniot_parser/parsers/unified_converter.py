from .all_files_parsers import (
    BareketFileConverter,
    DefualtFileConverter,
    SuperPharmFileConverter,
    VictoryFileConverter,
    ShufersalFileConverter,
    CofixFileConverter,
    MahsaniAShukPromoFileConverter,
    SalachDabachFileConverter,
)
from kniot_parser.utils import Logger


class UnifiedConverter(object):
    """
    unified converter across all types and sources
    """

    parsers = {
        "bareket": BareketFileConverter,
        "mahsani a shuk": MahsaniAShukPromoFileConverter,
        "Victory": VictoryFileConverter,
        "Super-Pharm": SuperPharmFileConverter,
        "Shufersal": ShufersalFileConverter,
        "cofix": CofixFileConverter,
        "salachdabach": SalachDabachFileConverter,
    }
    defult_parser = DefualtFileConverter

    def __init__(self, store_name, file_type) -> None:
        self.file_type_parser = (
            self.parsers[store_name]()
            if store_name in self.parsers
            else self.defult_parser()
        ).get(file_type)

        self.file_type = file_type
        self.store_name = store_name

    def should_convert_to_incremental(self):
        """should we convert this file to incremenal to save storage"""
        return self.file_type_parser.is_full_data_snapshot()

    def get_key_column(self):
        """the key check document is index base on"""
        return self.file_type_parser.get_id()

    def convert(self, file, row_limit=None):
        """convert a file base on the type,chain"""
        Logger.info(f" converting file {file}.")
        data_frame = self.file_type_parser.convert(file, row_limit=row_limit)

        Logger.info(f"file {file}, dataframe shape is {data_frame.shape}")
        data_frame = self.drop_duplicate(data_frame)

        Logger.info(
            f"file {file}, after duplicate drop, dataframe shape is {data_frame.shape}"
        )

        data_frame = self.drop_duplicate_missing_inforamtion(data_frame)

        return self.adjust_to_file_type(data_frame)

    def drop_duplicate(self, data_frame):
        """drop duplicate entries in the database"""
        unique_rows = data_frame.astype("str").drop_duplicates().index

        if not unique_rows.empty:
            Logger.info(
                f"Droping {data_frame.shape[0]-unique_rows.shape[0]} duplicate entries."
            )
            return data_frame.iloc[unique_rows, :]
        return data_frame

    def drop_duplicate_missing_inforamtion(self, data_frame):
        def group_function(data):
            if data.shape[0] == 1:
                return data.head(1)
            elif data.shape[0] == 2:
                change = data.loc[:, ~(data.iloc[0] == data.iloc[1]).values]
                if (
                    change.shape[1] == 1
                    and "UnitQty" in change.columns
                    #                    and "Unknown " in change["UnitQty"].values
                ):
                    return data.tail(1)
                else:
                    raise ValueError(f"Change of {change} is not detected.")
            else:
                raise ValueError("Don't support duplicate for more the 2 rows.")

        if not data_frame.empty:
            if (data_frame[self.file_type_parser.get_id()].value_counts() > 1).any():
                return (
                    data_frame.groupby(self.file_type_parser.get_id())
                    .apply(group_function)
                    .reset_index(drop=True)
                )

        return data_frame

    def adjust_to_file_type(self, data_frame):
        data_frame.columns = map(lambda x: x.lower(), data_frame.columns)

        if self.file_type == "stores":
            columns_nan_mapping = {
                "subchainid": "not_apply",
                "subchainname": "not_apply",
                "chainid": "seems_redundant",
                "lastupdatedate": "never",
                "lastupdatetime": "never",
            }
            ignore_columns = ["latitude", "longitude"]
            rename = {}

        elif self.file_type == "pricefull":
            columns_nan_mapping = {"itemid": "not_apply", "itemtype": "not_apply"}
            ignore_columns = []
            rename = {"blsweighted": "bisweighted", "itemnm": "itemname"}
        elif self.file_type == "price":
            columns_nan_mapping = {"itemid": "not_apply"}
            ignore_columns = []
            rename = {"itemnm": "itemname"}
        elif self.file_type == "promo":
            columns_nan_mapping = {}
            ignore_columns = []
            rename = {}
        elif self.file_type == "promofull":
            columns_nan_mapping = {}
            ignore_columns = []
            rename = {}

        for column, fill_value in columns_nan_mapping.items():
            data_frame[column] = fill_value

        data_frame = data_frame.drop(columns=ignore_columns, errors="ignore")
        data_frame = data_frame.rename(columns=rename)

        return data_frame
