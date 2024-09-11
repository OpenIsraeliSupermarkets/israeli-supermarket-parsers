# import pandas as pd
# from il_supermarket_parsers.utils.multi_prcoessing import MultiProcessor, ProcessJob
# from il_supermarket_parsers.utils import read_dump_folder
# from .unified_converter import UnifiedConverter


# class ConvertingToDataFrame(ProcessJob):
#     """converting a file to data frame"""

#     def job(self, **kwargs):
#         store_name = kwargs.get("store_name")
#         file_type = kwargs.get("file_type")
#         full_path = kwargs.get("full_path")
#         converter = UnifiedConverter(store_name, file_type)
#         return converter.convert(full_path)


# class MultiUnifiedConverter(MultiProcessor):
#     """run multipcrossing converter"""

#     def __init__(self, dump_folder, file_type, number_of_processes=6):
#         super().__init__(number_of_processes)
#         self.dump_folder = dump_folder
#         self.file_type = file_type

#     def task_to_execute(self):
#         return ConvertingToDataFrame

#     def get_arguments_list(self):
#         """create list of arguments"""
#         data = read_dump_folder(folder=self.dump_folder)
#         data = data[data.file_type == self.file_type][
#             ["store_name", "file_type", "full_path"]
#         ]
#         return data.to_dict("records")

#     def post(self, results):
#         return pd.concat(results).reset_index(drop=True)
