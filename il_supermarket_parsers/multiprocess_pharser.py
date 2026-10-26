import asyncio
import threading
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .queue_worker import run_queue_worker
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
from .utils.data_loaders.queue_router import QueueRouter, WorkerDispatcher


class ParallelParserParams(BaseModel):
    """Runtime parameters for :class:`ParallelParser`."""

    enabled_parsers: List[str]
    enabled_file_types: List[str]
    source_configuration: SourceConfiguration
    output_configuration: List[OutputConfiguration]
    status_configuration: StatusConfiguration
    max_queue_size: int = Field(default=0, ge=0)

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


class QueueWorkerProcessing(ProcessJob):
    """Parse every pair the dispatcher sends to one worker inbox."""

    def job(self, **kwargs):
        """Run the worker loop until the dispatcher stops it."""
        asyncio.run(
            run_queue_worker(
                inbox=kwargs["inbox"],
                output_configuration=kwargs["output_configuration"],
                status_configuration=kwargs["status_config"],
                limit=kwargs.get("limit"),
                worker_index=kwargs.get("worker_index", 0),
            )
        )


class ParallelParser(MultiProcessor):
    """run insert task on parallel

    Folder sources run one pool job per (parser, file type). Queue sources run
    one long-lived worker per process slot instead: routers send each file to
    the worker that owns its pair, through inboxes capped at ``max_queue_size``.
    Every inbox has a running reader, so the cap cannot stall a router.
    """

    def __init__(
        self,
        params: ParallelParserParams,
        multiprocessing: int = 6,
    ):
        super().__init__(multiprocessing=multiprocessing)
        self.params = params
        self._routers: Dict[str, QueueRouter] = {}
        self._dispatcher: Optional[WorkerDispatcher] = None
        self._routing_started = False

    def _is_queue_source(self) -> bool:
        return isinstance(self.params.source_configuration, QueueSourceConfiguration)

    def task_to_execute(self):
        """the task to execute"""
        if self._is_queue_source():
            return QueueWorkerProcessing
        return RawProcessing

    def _worker_count(self) -> int:
        return max(1, self.multiprocessing or 0)

    def _setup_queue_routing(self) -> None:
        """Create the worker inboxes and one router per scraper queue."""
        if not self._is_queue_source() or self._dispatcher is not None:
            return

        self._dispatcher = WorkerDispatcher(
            worker_count=self._worker_count(),
            enabled_parsers=self.params.enabled_parsers,
            enabled_file_types=self.params.enabled_file_types,
            max_queue_size=self.params.max_queue_size,
        )
        queue_handlers = self.params.source_configuration.queue_handlers
        for scraper_name, handler in queue_handlers.items():
            self._routers[scraper_name] = QueueRouter(
                scraper_name,
                handler,
                self.params.enabled_file_types,
                dispatcher=self._dispatcher,
            )

        Logger.info(
            "Set up queue routing for %d scrapers into %d workers (inbox cap %s)",
            len(self._routers),
            len(self._dispatcher.inboxes),
            self.params.max_queue_size or "unbounded",
        )

    def on_workers_started(self) -> None:
        """Start the routers and their coordinator once the pool has forked."""
        if self._dispatcher is None or self._routing_started:
            return
        self._routing_started = True
        for router in self._routers.values():
            router.start()
        threading.Thread(
            target=self._finish_queue_routing,
            name="queue-router-coordinator",
            daemon=True,
        ).start()

    def _finish_queue_routing(self) -> None:
        """Once every router is done, close the remaining pairs and stop workers."""
        for router in self._routers.values():
            router.wait()
        self._dispatcher.end_all()
        self._dispatcher.stop_workers()

    def get_arguments_list(self, limit=None):
        """create list of arguments"""
        Logger.info(f"Creating combinations for {self.params.to_string()},")

        if self._is_queue_source():
            self._setup_queue_routing()
            return [
                {
                    "worker_index": index,
                    "inbox": inbox,
                    "limit": limit,
                    "output_configuration": self.params.output_configuration,
                    "status_config": self.params.status_configuration,
                }
                for index, inbox in enumerate(self._dispatcher.inboxes)
            ]

        params_order = [
            "limit",
            "store_enum",
            "file_type",
            "source_configuration",
            "output_configuration",
            "status_config",
        ]

        task_can_executed_independently = []
        for parser_name in self.params.enabled_parsers:
            for file_type in self.params.enabled_file_types:
                combo = (
                    limit,
                    parser_name,
                    file_type,
                    self.params.source_configuration,
                    self.params.output_configuration,
                    self.params.status_configuration,
                )
                task_can_executed_independently.append(dict(zip(params_order, combo)))

        return task_can_executed_independently
