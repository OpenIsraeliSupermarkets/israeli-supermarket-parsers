import asyncio
from typing import Dict, List, Optional

from pydantic import BaseModel

from .raw_parsing_pipeline import RawParsingPipeline
from .utils import (
    Logger,
    create_parser_status,
    get_data_loader,
    get_output_writer,
)
from .utils.multi_processing import MultiProcessor, ProcessJob
from .utils.types import (
    OutputConfiguration,
    QueueSourceConfiguration,
    SourceConfiguration,
    StatusConfiguration,
)
from .utils.data_loaders.queue_router import (
    QueueRouter,
    RoutedQueueWrapper,
)


class ParallelParserParams(BaseModel):
    """Runtime parameters for :class:`ParallelParser`."""

    enabled_parsers: List[str]
    enabled_file_types: List[str]
    source_configuration: SourceConfiguration
    output_configuration: List[OutputConfiguration]
    status_configuration: StatusConfiguration

    def to_string(self) -> str:
        """Summarize these params for logging."""
        return (
            f"parsers={self.enabled_parsers},"
            f"file_types={self.enabled_file_types},"
            f"output_configuration={self.output_configuration},"
            f"status_configuration={self.status_configuration},"
            f"source_configuration={self.source_configuration},"
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
                    enabled_file_types=file_type,
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
        self._routers: Dict[str, QueueRouter] = {}
        self._routed_handlers: Optional[
            Dict[str, Dict[str, RoutedQueueWrapper]]
        ] = None

    def task_to_execute(self):
        """the task to execute"""
        return RawProcessing

    def _setup_queue_routing(self) -> None:
        """Set up queue routing when source is queue-based.

        Creates a QueueRouter for each scraper, which reads from the scraper
        queue and routes messages to per-file-type internal queues.
        """
        source_config = self.params.source_configuration
        if not isinstance(source_config, QueueSourceConfiguration):
            return

        if self._routed_handlers is not None:
            return

        self._routed_handlers = {}
        for scraper_name, handler in source_config.queue_handlers.items():
            router = QueueRouter(
                scraper_name, handler, self.params.enabled_file_types
            )
            self._routers[scraper_name] = router

            self._routed_handlers[scraper_name] = {}
            for file_type in self.params.enabled_file_types:
                self._routed_handlers[scraper_name][file_type] = (
                    router.get_routed_handler(file_type)
                )

            router.start()

        Logger.info(
            "Set up queue routing for %d scrapers with %d file types each",
            len(self._routers),
            len(self.params.enabled_file_types),
        )

    def _get_source_config_for_job(
        self, parser_name: str, file_type: str
    ) -> SourceConfiguration:
        """Get the source configuration for a specific (parser, file_type) job.

        For folder sources, returns the original configuration.
        For queue sources, returns a configuration with only the routed queue
        for this specific (parser, file_type) combination.
        """
        source_config = self.params.source_configuration
        if not isinstance(source_config, QueueSourceConfiguration):
            return source_config

        if self._routed_handlers is None:
            self._setup_queue_routing()

        if parser_name not in self._routed_handlers:
            Logger.warning(
                "No routed handler for parser %s, using empty queue handlers",
                parser_name,
            )
            return QueueSourceConfiguration(queue_handlers={})

        routed_handler = self._routed_handlers[parser_name].get(file_type)
        if routed_handler is None:
            Logger.warning(
                "No routed handler for %s/%s, using empty queue handlers",
                parser_name,
                file_type,
            )
            return QueueSourceConfiguration(queue_handlers={})

        return QueueSourceConfiguration(
            queue_handlers={parser_name: routed_handler}
        )

    def get_arguments_list(self, limit=None):
        """create list of arguments"""
        self._setup_queue_routing()

        params_order = [
            "limit",
            "store_enum",
            "file_type",
            "source_configuration",
            "output_configuration",
            "status_config",
        ]

        Logger.info(f"Creating combinations for {self.params.to_string()},")

        task_can_executed_independently = []
        for parser_name in self.params.enabled_parsers:
            for file_type in self.params.enabled_file_types:
                source_config = self._get_source_config_for_job(
                    parser_name, file_type
                )
                combo = (
                    limit,
                    parser_name,
                    file_type,
                    source_config,
                    self.params.output_configuration,
                    self.params.status_configuration,
                )
                task_can_executed_independently.append(
                    dict(zip(params_order, combo))
                )

        return task_can_executed_independently
