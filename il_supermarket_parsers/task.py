import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pytz

from .multiprocess_pharser import ParallelParser, ParallelParserParams
from .parser_factory import ParserFactory
from .utils.logger import Logger
from .utils.output_writers import ParsedRowsQueue, create_output_queue


def _default_when_date() -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("Asia/Jerusalem"))


@dataclass
class ConvertingTaskConfig:
    """Configuration for :class:`ConvertingTask` (supports ``ConvertingTask(**kwargs)``)."""

    data_folder: str = "dumps"
    enabled_parsers: Optional[list] = None
    files_types: Optional[list] = None
    multiprocessing: int = 6
    limit: Optional[int] = None
    when_date: datetime.datetime = field(default_factory=_default_when_date)
    output_folder: str = "outputs"
    queue_handlers: Optional[Dict[str, Any]] = None
    kafka_config: Optional[Dict[str, Any]] = None
    status_configuration: Optional[Dict[str, Any]] = None
    output_configuration: Optional[Dict[str, Any]] = None


class OutputQueueResult:
    """Returned by ConvertingTask.consume() – holds the consumer-side queue handle."""

    def __init__(self, queue_handler: ParsedRowsQueue):
        self.queue_handler = queue_handler

    def get_queue(self) -> ParsedRowsQueue:
        """Return the underlying queue handle."""
        return self.queue_handler


class ConvertingTask:
    """main convert task"""

    def __init__(
        self,
        config: Optional[ConvertingTaskConfig] = None,
        **kwargs: Any,
    ) -> None:
        cfg = config or ConvertingTaskConfig(**kwargs)
        Logger.info(
            f"Starting Parser, data_folder={cfg.data_folder},"
            f"number_of_processes={cfg.multiprocessing}"
            f"parsers = {cfg.enabled_parsers}"
            f"files_types = {cfg.files_types}"
            f"output_folder={cfg.output_folder}"
            f"limit={cfg.limit}"
            f"when_date={cfg.when_date}"
            f"queue_handlers={'provided' if cfg.queue_handlers else 'None'}"
            f"kafka_config={'provided' if cfg.kafka_config else 'None'}"
            f"status_configuration={cfg.status_configuration}"
            f"output_configuration={cfg.output_configuration}"
        )

        self._config = cfg

        # Build per-parser output queues when queue output mode is requested
        self._output_queues = {}
        if cfg.output_configuration and cfg.output_configuration.get("output_mode") == "queue":
            parsers = cfg.enabled_parsers or ParserFactory.all_parsers_name()
            for parser_name in parsers:
                self._output_queues[parser_name] = create_output_queue()

        self.runner = ParallelParser(
            ParallelParserParams(
                data_folder=cfg.data_folder,
                enabled_parsers=cfg.enabled_parsers,
                enabled_file_types=cfg.files_types,
                output_folder=cfg.output_folder,
                when_date=cfg.when_date,
                queue_handlers=cfg.queue_handlers,
                kafka_config=cfg.kafka_config,
                status_configuration=cfg.status_configuration,
                output_queues=self._output_queues if self._output_queues else None,
            ),
            multiprocessing=cfg.multiprocessing,
        )
        self.limit = cfg.limit

    def consume(self) -> Dict[str, OutputQueueResult]:
        """Return a dict mapping parser names to OutputQueueResult objects.

        Must be called before start() so queue handles are ready for consumers.
        Only returns entries when output_configuration was set to queue mode.
        """
        return {
            name: OutputQueueResult(queue_handler=ParsedRowsQueue(q))
            for name, q in self._output_queues.items()
        }

    def start(self):
        """Run the parsing synchronously and return execution results.

        When queue output mode is active, a None sentinel is placed in every
        output queue after processing completes so consumers can detect the end.
        """
        result = self.runner.execute(limit=self.limit)
        for q in self._output_queues.values():
            q.put(None)
        return result
