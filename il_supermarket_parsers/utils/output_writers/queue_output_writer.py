import multiprocessing
from typing import List
from .base_output_writer import BaseOutputWriter
from ..logger import Logger


_manager = None


def _get_manager():
    global _manager
    if _manager is None:
        _manager = multiprocessing.Manager()
    return _manager


class ParsedRowsQueue:
    """Consumer handle for a parsed-output queue. Thread/process-safe."""

    def __init__(self, queue):
        self._queue = queue

    def get(self):
        """Return the next parsed row dict, or None when the stream ends."""
        return self._queue.get()


def create_output_queue():
    """Create a new process-safe queue for parsed row output."""
    return _get_manager().Queue()


class QueueOutputWriter(BaseOutputWriter):
    """Output writer that enqueues parsed rows into a process-safe queue."""

    def __init__(self, queue):
        self._queue = queue

    async def write_row(self, row: dict) -> None:
        Logger.debug(f"Enqueuing parsed row: {list(row.keys())}")
        self._queue.put(row)

    async def initialize(self) -> None:
        pass

    def exists(self) -> bool:
        return True

    def get_path(self) -> str:
        return "memory_queue"

    def get_existing_columns(self) -> List[str]:
        return []
