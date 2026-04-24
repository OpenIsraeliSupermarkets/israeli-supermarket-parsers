import datetime
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pytz

from .multiprocess_pharser import ParallelParser, ParallelParserParams
from .parser_factory import ParserFactory
from .utils.logger import Logger
from .utils import FileTypesFilters
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
    """Encapsulates a parsing task that can be run in a separate thread.

    Example::

        task = ConvertingTask(data_folder="dumps", output_folder="outputs")
        task.start()
        task.join()

    With queue output::

        task = ConvertingTask(
            data_folder="dumps",
            output_configuration={"output_mode": "queue"},
        )
        queues = task.consume()
        task.start()
        for name, result in queues.items():
            for row in iter(result.get_queue().get, None):
                print(row)
        task.join()
    """

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
        self._thread = None

        # Build per-parser output queues when queue output mode is requested
        self._output_queues = {}
        if (
            cfg.output_configuration
            and cfg.output_configuration.get("output_mode") == "queue"
        ):
            parsers = cfg.enabled_parsers or ParserFactory.all_parsers_name()
            file_types = cfg.files_types or FileTypesFilters.all_types()
            for parser_name in parsers:
                for file_type in file_types:
                    self._output_queues[(parser_name, file_type)] = (
                        create_output_queue()
                    )

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

    def consume(self) -> Dict[str, OutputQueueResult]:
        """Return a dict mapping parser names to OutputQueueResult objects.

        Call before start() so queue handles are ready for consumers.
        Only returns entries when output_configuration was set to queue mode.
        """
        return {
            name: OutputQueueResult(queue_handler=ParsedRowsQueue(q))
            for name, q in self._output_queues.items()
        }

    def start(self, limit: Optional[int] = None) -> threading.Thread:
        """Start the parsing task in a new background thread.

        Args:
            limit: Maximum number of files to process. If None, processes all.

        Returns:
            The thread running the parsing task.

        Raises:
            RuntimeError: If parsing is already running.
        """
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("Parsing is already running")

        def _run():
            try:
                self.runner.execute(limit=limit)
            finally:
                for q in self._output_queues.values():
                    q.put(None)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        return self._thread

    def join(self) -> bool:
        """Wait for the parsing thread to complete.

        Returns:
            True if the thread was joined successfully.

        Raises:
            RuntimeError: If parsing is not running.
        """
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()
            return True
        raise RuntimeError("Parsing is not running")

    def stop(self) -> None:
        """Terminate worker processes and stop the parsing task."""
        for process in self.runner.processes:
            if process.is_alive():
                Logger.warning(f"Terminating process {process.name}")
                process.terminate()
                process.join(timeout=5)
