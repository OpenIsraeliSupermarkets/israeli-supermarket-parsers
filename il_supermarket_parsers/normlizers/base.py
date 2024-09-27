# # from il_supermarket_parsers.utils import Logger
# from abc import ABC


# class DataFrameNormlizer(ABC):
#     """
#     converting dataframe to a normlize form
#     """

#     def __init__(self) -> None:
#         pass

#     def normlize(self, file, data_frame, row_limit=None):
#         pass

#     # def _normlize_columns(
#     #         data,
#     #         missing_columns_default_values,
#     #         columns_to_remove,
#     #         columns_to_rename,
#     #         date_columns=None,
#     #         float_columns=None,
#     #         empty_value="NOT_APPLY",
#     #         **_,
#     #     ):
#     #         if date_columns and not data.empty:
#     #             for column in date_columns:
#     #                 data[column] = pd.to_datetime(data[column])

#     #         if float_columns and not data.empty:
#     #             for column in float_columns:
#     #                 data[column] = pd.to_numeric(data[column])
#     #         data = data.fillna(empty_value)

#     #         #
#     #         for column, fill_value in missing_columns_default_values.items():
#     #             if column not in data.columns:

#     #                 if isinstance(fill_value, str):
#     #                     data[column] = fill_value
#     #                 else:
#     #                     data[column] = fill_value()

#     #         data = data.drop(columns=columns_to_remove, errors="ignore")
#     #         return data.rename(columns=columns_to_rename)

#     # def load_column_config(self, json_key):
#     #     with open("il_supermarket_parsers/conf/processing.json") as file:
#     #         return json.load(file)[json_key]
