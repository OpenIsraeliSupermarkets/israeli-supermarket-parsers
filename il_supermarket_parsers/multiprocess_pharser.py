import itertools
import datetime
import os
import pytz
import asyncio
from .raw_parsing_pipeline import ExecutionLog, RawParsingPipeline
from .utils.multi_processing import MultiProcessor, ProcessJob
from .utils.parser_status import create_parser_status
from .parser_factory import ParserFactory
from .utils import FileTypesFilters, Logger, DataLoader, CSVOutputWriter


class RawProcessing(ProcessJob):
    """converting file to database"""

    def job(self, **kwargs):
        """read the dump folder and filter according to the requested filters
        start processing file according to thier "update_date"
        """
        queue_handlers = kwargs.pop("queue_handlers", None)
        kafka_config = kwargs.pop("kafka_config", None)
        drop_folder = kwargs.pop("data_folder", None)
        file_type = kwargs.pop("file_type")
        parser_name = kwargs.pop("store_enum")
        output_folder = kwargs.pop("output_folder", None)
        limit = kwargs.pop("limit")
        status_config = kwargs.pop("status_config", None)

        if queue_handlers:
            from .utils import QueueDataLoader
            data_loader = QueueDataLoader(queue_handlers)
        else:
            data_loader = DataLoader(
                drop_folder,
                store_names=[parser_name],
                files_types=[file_type],
            )

        if kafka_config:
            from .utils import KafkaOutputWriter
            output_writer = KafkaOutputWriter(
                bootstrap_servers=kafka_config["bootstrap_servers"],
                topic=kafka_config["topic"],
                key_columns=kafka_config.get("key_columns"),
            )
        else:
            output_path = os.path.join(
                output_folder,
                file_type.lower() + "_" + parser_name.lower() + ".csv",
            )
            output_writer = CSVOutputWriter(output_path)

        database_name = f"{parser_name}_{file_type}".lower()
        parser_status = create_parser_status(
            database_name,
            status_configuration=status_config,
            default_base_path=output_folder or "outputs",
        )

        pipeline = RawParsingPipeline(
            data_loader=data_loader,
            output_writer=output_writer,
            parser_status=parser_status,
        )

        try:
            asyncio.run(
                pipeline.process(
                    limit=limit,
                    store_names=[parser_name],
                    files_types=[file_type],
                )
            )
        finally:
            if kafka_config:
                output_writer.close()


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
        queue_handlers=None,
        kafka_config=None,
        status_configuration=None,
    ):
        super().__init__(multiprocessing=multiprocessing)
        self.data_folder = data_folder
        self.enabled_parsers = enabled_parsers
        self.enabled_file_types = enabled_file_types
        self.output_folder = output_folder
        self.when_date = when_date
        self.queue_handlers = queue_handlers
        self.kafka_config = kafka_config
        self.status_configuration = status_configuration

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
            "queue_handlers",
            "kafka_config",
            "status_config",
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
                [self.queue_handlers],
                [self.kafka_config],
                [self.status_configuration],
            )
        )
        task_can_executed_independently = [
            dict(zip(params_order, combo)) for combo in combinations
        ]
        return task_can_executed_independently

    def post(self, results):
        """post process the results"""
        return super().post(results)
