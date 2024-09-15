from .raw_parsing_pipeline import RawParseingPipeline
from .utils.multi_prcoessing import MultiProcessor, ProcessJob
from .utils.logger import Logger
from parser_factroy import ParserFactory
from utils import FileTypesFilters
import itertools


class UploadRawToKaggle(ProcessJob):
    """converting file to database"""

    def job(self, **kwargs):
        """read the dump folder and filter according to the requested filters
        start processing file according to thier "update_date"
        """
        # take args
        drop_folder = kwargs.pop("data_folder")
        file_type = kwargs.pop("file_type")
        parser_name = kwargs.pop("type")
        parser_enum = ParserFactory.get(parser_name)

        RawParseingPipeline(drop_folder, parser_enum, file_type).process()


class ParallelParser(MultiProcessor):
    """run insert task on parallel"""

    def __init__(self, data_folder, number_of_processes=6):
        super().__init__(number_of_processes=number_of_processes)
        self.data_folder = data_folder

    def task_to_execute(self):
        """the task to execute"""
        return UploadRawToKaggle

    def get_arguments_list(self):
        """create list of arguments"""

        all_parsers = ParserFactory.all_listed_parsers()
        all_file_types = FileTypesFilters.all_types()
        params_order = ["type", "file_type", "data_folder"]
        combinations = list(
            itertools.product(
                all_parsers, all_file_types, all_file_types, self.data_folder
            )
        )
        task_can_executed_indepentlly = [
            dict(zip([params_order], combo)) for combo in combinations
        ]
        return task_can_executed_indepentlly
