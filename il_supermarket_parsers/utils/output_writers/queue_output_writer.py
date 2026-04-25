import multiprocessing
from typing import Any, List

from .base_output_writer import BaseOutputWriter
from ..types import FileCompleteMessage


class _QueueManagerHolder:
    """Lazily create one shared ``multiprocessing.Manager()`` for queue output."""

    _instance: Any = None

    @classmethod
    def manager(cls) -> Any:
        """Return a shared ``multiprocessing.Manager`` (singleton)."""
        if cls._instance is None:
            cls._instance = multiprocessing.Manager()
        return cls._instance


class ParsedRowsQueue:
    """Consumer handle for a parsed-output queue. Thread/process-safe."""

    def __init__(self, queue):
        self._queue = queue

    def get(self):
        """Return the next parsed row dict, or None when the stream ends."""
        return self._queue.get()

    def put(self, item) -> None:
        """Put an item (e.g. end sentinel) onto the underlying queue."""
        self._queue.put(item)

    def get_all_messages(self):
        """Iterate parsed rows until the None end-of-stream sentinel."""
        return iter(self._queue.get, None)


def create_output_queue():
    """Create a new process-safe queue for parsed row output."""
    return _QueueManagerHolder.manager().Queue()


class QueueOutputWriter(BaseOutputWriter):
    """Output writer that enqueues parsed rows into a process-safe queue."""

    def __init__(self, queue):
        self._queue = queue

    async def write_row(self, row: dict) -> None:
        self._queue.put(row)

    async def write_file_complete(self, message: FileCompleteMessage) -> None:
        self._queue.put(message.model_dump())

    async def initialize(self) -> None:
        """No-op for in-memory queue output."""
        return

    def exists(self) -> bool:
        return True

    def get_path(self) -> str:
        return "memory_queue"

    def get_existing_columns(self) -> List[str]:
        return []

    def close(self) -> None:
        self._queue.put(None)
