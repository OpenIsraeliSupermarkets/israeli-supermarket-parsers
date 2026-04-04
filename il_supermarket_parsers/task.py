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
        queue_handlers=None,
        kafka_config=None,
        status_configuration=None,
    ):
        Logger.info(
            f"Starting Parser, data_folder={data_folder},"
            f"number_of_processes={multiprocessing}"
            f"parsers = {enabled_parsers}"
            f"files_types = {files_types}"
            f"output_folder={output_folder}"
            f"limit={limit}"
            f"when_date={when_date}"
            f"queue_handlers={'provided' if queue_handlers else 'None'}"
            f"kafka_config={'provided' if kafka_config else 'None'}"
            f"status_configuration={status_configuration}"
        )
        self.runner = ParallelParser(
            data_folder,
            enabled_parsers=enabled_parsers,
            enabled_file_types=files_types,
            multiprocessing=multiprocessing,
            output_folder=output_folder,
            when_date=when_date,
            queue_handlers=queue_handlers,
            kafka_config=kafka_config,
            status_configuration=status_configuration,
        )
        self.limit = limit

    def start(self):
        """run the parsing"""
        return self.runner.execute(limit=self.limit)
