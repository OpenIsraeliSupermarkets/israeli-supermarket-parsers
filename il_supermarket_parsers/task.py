import datetime
import pytz
from .multiprocess_pharser import ParallelParser
from .utils.logger import Logger


class ConvertingTask:
    """main convert task"""

    def __init__(
        self,
        data_folder="dumps",
        enabled_parsers=None,
        files_types=None,
        multiprocessing=6,
        limit=None,
        when_date=datetime.datetime.now(pytz.timezone("Asia/Jerusalem")),
        output_folder="outputs",
    ):
        Logger.info(
            f"Starting Parser, data_folder={data_folder},"
            f"number_of_processes={multiprocessing}"
            f"parsers = {enabled_parsers}"
            f"files_types = {files_types}"
            f"output_folder={output_folder}"
            f"limit={limit}"
            f"when_date={when_date}"
        )
        self.runner = ParallelParser(
            data_folder,
            enabled_parsers=enabled_parsers,
            enabled_file_types=files_types,
            multiprocessing=multiprocessing,
            output_folder=output_folder,
            when_date=when_date,
        )
        self.limit = limit

    def start(self):
        """run the parsing"""
        return self.runner.execute(limit=self.limit)
