import os
import threading
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from .multiprocess_pharser import ParallelParser, ParallelParserParams
from .parser_factory import ParserFactory
from .utils import FileTypesFilters
from .utils.output_writers import ParsedRowsQueue, create_output_queue
from .utils.types import (
    OutputConfiguration,
    SourceConfiguration,
    StatusConfiguration,
    QueueOutputConfiguration,
    CsvOutputConfiguration,
)


class ConvertingTaskConfig(BaseModel):
    """Configuration for :class:`ConvertingTask` (supports ``ConvertingTask(**kwargs)``)."""

    source_configuration: SourceConfiguration
    output_configuration: List[OutputConfiguration]
    status_configuration: StatusConfiguration
    multiprocessing: int = 6
    enabled_parsers: Optional[list] = None
    files_types: Optional[list] = None

    def get_enabled_parsers(self) -> List[str]:
        """Return configured parser names, or all parsers if none are set."""
        return self.enabled_parsers or ParserFactory.all_parsers_name()

    def get_enabled_file_types(self) -> List[str]:
        """Return configured file types, or all types if none are set."""
        return self.files_types or FileTypesFilters.all_types()


class ConvertingTask:
    """Encapsulates a parsing task that can be run in a separate thread.

    Example::

        task = ConvertingTask(
            source_configuration={"folder": "dumps"},
            output_configuration={"output_folder": "outputs"},
        )
        task.start()
        task.join()

    With queue output::

        task = ConvertingTask(
            source_configuration={"queue_handlers": scraper.consume()},
            output_configuration={"output_mode": "queue"},
        )
        queues = task.consume()
        task.start()
        for name, result in queues.items():
            for row in iter(result.get_queue().get, None):
                print(row)
        task.join()

    With multiple outputs (queue + CSV)::

        task = ConvertingTask(
            source_configuration={"queue_handlers": scraper.consume()},
            output_configuration=[
                {"output_mode": "queue"},
                {"output_mode": "csv", "output_folder": "outputs"},
            ],
        )
    """

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        self._config = ConvertingTaskConfig(**kwargs)
        self._thread = None

        # Build per-parser output queues when any config requests queue output
        self._output_queues = {}
        for output_configuration in self._config.output_configuration:
            if isinstance(output_configuration, QueueOutputConfiguration):
                parsers = self._config.get_enabled_parsers()
                file_types = self._config.get_enabled_file_types()
                for parser_name in parsers:
                    for file_type in file_types:
                        self._output_queues[(parser_name, file_type)] = (
                            create_output_queue()
                        )
                output_configuration.queues = self._output_queues

            elif isinstance(output_configuration, CsvOutputConfiguration):
                os.makedirs(output_configuration.output_folder, exist_ok=True)

        self.runner = ParallelParser(
            ParallelParserParams(
                enabled_parsers=self._config.get_enabled_parsers(),
                enabled_file_types=self._config.get_enabled_file_types(),
                source_configuration=self._config.source_configuration,
                output_configuration=self._config.output_configuration,
                status_configuration=self._config.status_configuration,
            ),
            multiprocessing=self._config.multiprocessing,
        )

    def consume(self) -> Dict[Tuple[str, str], ParsedRowsQueue]:
        """Return a dict mapping (parser, file_type) tuples to ParsedRowsQueue handles.

        Call before start() so queue handles are ready for consumers.
        Only returns entries when output_configuration was set to queue mode.
        """
        return {name: ParsedRowsQueue(q) for name, q in self._output_queues.items()}

    def start(
        self,
        limit: Optional[int] = None,
    ) -> threading.Thread:
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
        """Terminate the worker pool and stop the parsing task."""
        self.runner.terminate()
