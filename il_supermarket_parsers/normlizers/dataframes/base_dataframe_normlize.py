# from il_supermarket_parsers.utils import Logger
# from abc import ABC, abstractmethod


# class BaseDataFrameNormlizer(ABC):
#     """
#     unified converter across all types and sources
#     """

#     def __init__(
#         self,
#     ) -> None:
#         pass

#     def normlize(self, file, data_frame, file_type, index):
#         """normlizing a file base on the type,chain"""
#         Logger.info(f" converting file {file}.")

#         data_frame = data_frame.replace(r"\n", " ", regex=True)
#         data_frame = data_frame.replace(r"\r", " ", regex=True)

#         Logger.info(f"file {file}, dataframe shape is {data_frame.shape}")
#         data_frame = self.drop_duplicate(data_frame)

#         Logger.info(
#             f"file {file}, after duplicate drop, dataframe shape is {data_frame.shape}"
#         )

#         data_frame = self.drop_duplicate_missing_inforamtion(data_frame, index)

#         return self._typing_normlize(data_frame, file_type)

#     def drop_duplicate_missing_inforamtion(self, data_frame, index):
#         def group_function(data):
#             if data.shape[0] == 1:
#                 return data.head(1)
#             elif data.shape[0] == 2:
#                 change = data.loc[:, ~(data.iloc[0] == data.iloc[1]).values]
#                 if (
#                     change.shape[1] == 1
#                     and "UnitQty" in change.columns
#                     #                    and "Unknown " in change["UnitQty"].values
#                 ):
#                     return data.tail(1)
#                 else:
#                     raise ValueError(f"Change of {change} is not detected.")
#             else:
#                 raise ValueError("Don't support duplicate for more the 2 rows.")

#         if not data_frame.empty:
#             if (data_frame[index].value_counts() > 1).any():
#                 return (
#                     data_frame.groupby(index)
#                     .apply(group_function)
#                     .reset_index(drop=True)
#                 )

#         return data_frame

#     @abstractmethod
#     def _typing_normlize(data, file_type):
#         pass
