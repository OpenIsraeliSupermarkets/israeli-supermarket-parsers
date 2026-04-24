import itertools
import datetime
import os
import asyncio
from dataclasses import dataclass, field
from typing import Any, List, Optional

import pytz

from .raw_parsing_pipeline import RawParsingPipeline
from .utils.multi_processing import MultiProcessor, ProcessJob
from .utils.status import create_parser_status
from .parser_factory import ParserFactory
from .utils import FileTypesFilters, Logger, DataLoader, CSVOutputWriter
from .utils import QueueOutputWriter, KafkaOutputWriter
from .utils import QueueDataLoader


def _default_parallel_when() -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("Asia/Jerusalem"))


@dataclass
class ParallelParserParams:
    """Runtime parameters for :class:`ParallelParser`."""

    data_folder: str
    enabled_parsers: Optional[List[str]] = None
    enabled_file_types: Optional[List[str]] = None
    output_folder: str = "output"
    when_date: datetime.datetime = field(default_factory=_default_parallel_when)
    queue_handlers: Any = None
    kafka_config: Any = None
    status_configuration: Any = None
    output_queues: Any = None

    def get_enabled_parsers(self) -> List[str]:
        """Return configured parser names, or all parsers if none are set."""
        return self.enabled_parsers or ParserFactory.all_parsers_name()

    def get_enabled_file_types(self) -> List[str]:
        """Return configured file types, or all types if none are set."""
        return self.enabled_file_types or FileTypesFilters.all_types()

    def get_output_folder(self) -> str:
        """Return the base output directory path."""
        return self.output_folder

    def get_when_date(self) -> datetime.datetime:
        """Return the run timestamp (Jerusalem) used for filtering."""
        return self.when_date

    def to_string(self) -> str:
        """Summarize these params for logging."""
        return (
            f"parsers={self.get_enabled_parsers()},"
            f"file_types={self.get_enabled_file_types()},"
            f"data_folder={self.data_folder},"
            f"output_folder={self.get_output_folder()},"
            f"when_date={self.get_when_date().strftime('%Y-%m-%d %H:%M:%S %z')}"
        )


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
            data_loader = QueueDataLoader(queue_handlers)
        else:
            data_loader = DataLoader(drop_folder)

        output_queues = kwargs.pop("output_queues", None)

        if output_queues and parser_name in output_queues:
            output_writer = QueueOutputWriter(output_queues[parser_name])
        elif kafka_config:
            output_writer = KafkaOutputWriter(
                bootstrap_servers=kafka_config["bootstrap_servers"],
                key_columns=kafka_config.get("key_columns"),
                enabled_scraper=parser_name,
                enabled_file_type=file_type,
            )
        else:
            output_writer = CSVOutputWriter(output_folder, parser_name, file_type)

        parser_status = create_parser_status(
            enabled_scraper=parser_name,
            enabled_file_type=file_type,
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
                    enabled_scraper=parser_name,
                    enabled_file_types=[file_type],
                )
            )
        finally:
            if kafka_config:
                output_writer.close()


class ParallelParser(MultiProcessor):
    """run insert task on parallel"""

    def __init__(
        self,
        params: ParallelParserParams,
        multiprocessing: int = 6,
    ):
        super().__init__(multiprocessing=multiprocessing)
        self.params = params

    def task_to_execute(self):
        """the task to execute"""
        return RawProcessing

    def get_arguments_list(self, limit=None):
        """create list of arguments"""

        os.makedirs(self.params.output_folder, exist_ok=True)

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
            "output_queues",
        ]

        Logger.info(f"Creating combinations for {self.params.to_string()},")
        combinations = list(
            itertools.product(
                [limit],
                self.params.get_enabled_parsers(),
                self.params.get_enabled_file_types(),
                [self.params.data_folder],
                [self.params.output_folder],
                [self.params.when_date.strftime("%Y-%m-%d %H:%M:%S %z")],
                [self.params.queue_handlers],
                [self.params.kafka_config],
                [self.params.status_configuration],
                [self.params.output_queues],
            )
        )
        task_can_executed_independently = [
            dict(zip(params_order, combo)) for combo in combinations
        ]
        return task_can_executed_independently
