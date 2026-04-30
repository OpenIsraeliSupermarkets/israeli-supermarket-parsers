import itertools
import os
import asyncio
from dataclasses import dataclass
from typing import Any, List, Optional

from .raw_parsing_pipeline import RawParsingPipeline
from .utils.multi_processing import MultiProcessor, ProcessJob
from .parser_factory import ParserFactory
from .utils import (
    FileTypesFilters,
    Logger,
    create_parser_status,
    get_data_loader,
    get_output_writer,
)


@dataclass
class ParallelParserParams:
    """Runtime parameters for :class:`ParallelParser`."""

    enabled_parsers: Optional[List[str]] = None
    enabled_file_types: Optional[List[str]] = None
    source_configuration: Any = None
    output_configuration: Any = None
    status_configuration: Any = None

    def get_enabled_parsers(self) -> List[str]:
        """Return configured parser names, or all parsers if none are set."""
        return self.enabled_parsers or ParserFactory.all_parsers_name()

    def get_enabled_file_types(self) -> List[str]:
        """Return configured file types, or all types if none are set."""
        return self.enabled_file_types or FileTypesFilters.all_types()

    def get_output_folder(self) -> str:
        """Return the base output directory path."""
        cfg = self.output_configuration or {}
        return cfg.get("output_folder", "outputs")

    def to_string(self) -> str:
        """Summarize these params for logging."""
        src = self.source_configuration or {}
        return (
            f"parsers={self.get_enabled_parsers()},"
            f"file_types={self.get_enabled_file_types()},"
            f"data_folder={src.get('folder', 'dumps')},"
            f"output_folder={self.get_output_folder()},"
        )


class RawProcessing(ProcessJob):
    """converting file to database"""

    def job(self, **kwargs):
        """read the dump folder and filter according to the requested filters
        start processing file according to thier "update_date"
        """
        source_config = kwargs.pop("source_configuration", {})
        output_config = kwargs.pop("output_configuration", {})
        file_type = kwargs.pop("file_type")
        parser_name = kwargs.pop("store_enum")
        limit = kwargs.pop("limit", None)
        status_config = kwargs.pop("status_config", {})

        data_loader = get_data_loader(source_config)

        output_writer = get_output_writer(parser_name, file_type, output_config)

        parser_status = create_parser_status(
            enabled_scraper=parser_name,
            enabled_file_type=file_type,
            status_configuration=status_config,
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
            asyncio.run(output_writer.close())


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

        os.makedirs(self.params.get_output_folder(), exist_ok=True)

        params_order = [
            "limit",
            "store_enum",
            "file_type",
            "when_date",
            "source_configuration",
            "output_configuration",
            "status_config",
        ]

        Logger.info(f"Creating combinations for {self.params.to_string()},")
        combinations = list(
            itertools.product(
                [limit],
                self.params.get_enabled_parsers(),
                self.params.get_enabled_file_types(),
                [self.params.source_configuration],
                [self.params.output_configuration],
                [self.params.status_configuration],
            )
        )
        task_can_executed_independently = [
            dict(zip(params_order, combo)) for combo in combinations
        ]
        return task_can_executed_independently
