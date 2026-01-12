import itertools
import json
import datetime
import os
import pytz
from .raw_parsing_pipeline import ExecutionLog, RawParsingPipeline
from .utils.multi_processing import MultiProcessor, ProcessJob
from .parser_factory import ParserFactory
from .utils import FileTypesFilters, Logger, DataLoader, CSVOutputWriter


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
        when_date = kwargs.pop("when_date")

        # Create data loader
        data_loader = DataLoader(
            drop_folder,
            store_names=[parser_name],
            files_types=[file_type],
        )

        # Create output writer (CSV)
        output_path = os.path.join(
            output_folder,
            file_type.lower() + "_" + parser_name.lower() + ".csv",
        )
        output_writer = CSVOutputWriter(output_path)

        return RawParsingPipeline(
            store_name=parser_name,
            file_type=file_type,
            when_date=when_date,
            data_loader=data_loader,
            output_writer=output_writer,
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
        when_date=datetime.datetime.now(pytz.timezone("Asia/Jerusalem")),
    ):
        super().__init__(multiprocessing=multiprocessing)
        self.data_folder = data_folder
        self.enabled_parsers = enabled_parsers
        self.enabled_file_types = enabled_file_types
        self.output_folder = output_folder
        self.when_date = when_date

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
            "when_date",
        ]

        Logger.info(
            f"Creating combinations for limit={limit},"
            f"parsers={all_parsers},"
            f"file_types={all_file_types},"
            f"data_folder={self.data_folder},"
            f"output_folder={self.output_folder},"
            f"when_date={self.when_date.strftime('%Y-%m-%d %H:%M:%S %z')}"
        )
        combinations = list(
            itertools.product(
                [limit],
                all_parsers,
                all_file_types,
                [self.data_folder],
                [self.output_folder],
                [self.when_date.strftime("%Y-%m-%d %H:%M:%S %z")],
            )
        )
        task_can_executed_independently = [
            dict(zip(params_order, combo)) for combo in combinations
        ]
        return task_can_executed_independently

    def post(self, results):
        """post process the results"""
        status_file = os.path.join(self.output_folder, "parser-status.json")
        if os.path.exists(status_file):
            with open(status_file, "r", encoding="utf-8") as file:
                existing_results = json.load(file)
        else:
            existing_results = []

        # Convert ExecutionLog objects to dicts for JSON serialization
        serializable_results = []
        for result in results:
            if isinstance(result, dict) and "response" in result:
                # Check if response is an ExecutionLog object
                if isinstance(result["response"], ExecutionLog):
                    serializable_results.append(
                        {
                            **{k: v for k, v in result.items() if k != "response"},
                            "response": result["response"].to_dict(),
                        }
                    )
                else:
                    serializable_results.append(result)
            else:
                serializable_results.append(result)

        existing_results.extend(serializable_results)

        with open(status_file, "w", encoding="utf-8") as file:
            json.dump(existing_results, file)
        return super().post(results)
