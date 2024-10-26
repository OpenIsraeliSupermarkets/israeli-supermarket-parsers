import itertools
import json
import os
from .raw_parsing_pipeline import RawParsingPipeline
from .utils.multi_processing import MultiProcessor, ProcessJob
from .parser_factory import ParserFactory
from .utils import FileTypesFilters


class RawProcessing(ProcessJob):
    """converting file to database"""

    def job(self, **kwargs):
        """read the dump folder and filter according to the requested filters
        start processing file according to thier "update_date"
        """
        # take args
        drop_folder = kwargs.pop("data_folder")
        file_type = kwargs.pop("file_type")
        parser_name = kwargs.pop("store_enum")
        output_folder = kwargs.pop("output_folder")
        limit = kwargs.pop("limit")

        return RawParsingPipeline(
            drop_folder, parser_name, file_type, output_folder
        ).process(limit=limit)


class ParallelParser(MultiProcessor):
    """run insert task on parallel"""

    def __init__(
        self,
        data_folder,
        enabled_parsers=None,
        enabled_file_types=None,
        multiprocessing=6,
        output_folder="output",
    ):
        super().__init__(multiprocessing=multiprocessing)
        self.data_folder = data_folder
        self.enabled_parsers = enabled_parsers
        self.enabled_file_types = enabled_file_types
        self.output_folder = output_folder

    def task_to_execute(self):
        """the task to execute"""
        return RawProcessing

    def get_arguments_list(self, limit=None):
        """create list of arguments"""

        os.makedirs(self.output_folder, exist_ok=True)
        all_parsers = (
            self.enabled_parsers
            if self.enabled_parsers
            else ParserFactory.all_parsers_name()
        )
        all_file_types = (
            self.enabled_file_types
            if self.enabled_file_types
            else FileTypesFilters.all_types()
        )
        params_order = [
            "limit",
            "store_enum",
            "file_type",
            "data_folder",
            "output_folder",
        ]
        combinations = list(
            itertools.product(
                [limit],
                all_parsers,
                all_file_types,
                [self.data_folder],
                [self.output_folder],
            )
        )
        task_can_executed_independently = [
            dict(zip(params_order, combo)) for combo in combinations
        ]
        return task_can_executed_independently

    def post(self, results):
        """post process the results"""
        with open(
            os.path.join(self.output_folder, "parser-status.json"),
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(results, file)
        return super().post(results)
