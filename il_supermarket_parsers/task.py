import datetime
import pytz
from .multiprocess_pharser import ParallelParser
from .parser_factory import ParserFactory
from .utils.logger import Logger
from .utils.output_writers import ParsedRowsQueue, create_output_queue


class OutputQueueResult:
    """Returned by ConvertingTask.consume() – holds the consumer-side queue handle."""

    def __init__(self, queue_handler: ParsedRowsQueue):
        self.queue_handler = queue_handler


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
        output_configuration=None,
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
            f"output_configuration={output_configuration}"
        )

        # Build per-parser output queues when queue output mode is requested
        self._output_queues = {}
        if output_configuration and output_configuration.get("output_mode") == "queue":
            parsers = enabled_parsers or ParserFactory.all_parsers_name()
            for parser_name in parsers:
                self._output_queues[parser_name] = create_output_queue()

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
            output_queues=self._output_queues if self._output_queues else None,
        )
        self.limit = limit

    def consume(self):
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
