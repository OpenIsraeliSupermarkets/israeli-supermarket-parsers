import asyncio
from typing import List

from .base_output_writer import BaseOutputWriter
from ..types import FileCompleteMessage
from ..loading_utils import DumpFile


class MultiOutputWriter(BaseOutputWriter):
    """Fan-out writer that delegates every call concurrently to multiple writers."""

    def __init__(self, writers: List[BaseOutputWriter]):
        self._writers = writers

    async def initialize(self) -> None:
        await asyncio.gather(*(w.initialize() for w in self._writers))

    async def initialize_new_file(self, file: DumpFile) -> None:
        await asyncio.gather(*(w.initialize_new_file(file) for w in self._writers))

    async def write_row(self, row: dict) -> None:
        await asyncio.gather(*(w.write_row(row) for w in self._writers))

    async def write_file_complete(self, message: FileCompleteMessage) -> None:
        await asyncio.gather(*(w.write_file_complete(message) for w in self._writers))

    async def close(self) -> None:
        await asyncio.gather(*(w.close() for w in self._writers))

    def exists(self) -> bool:
        return any(w.exists() for w in self._writers)

    def get_path(self) -> str:
        return ",".join(w.get_path() for w in self._writers)

    def get_existing_columns(self) -> List[str]:
        seen = set()
        columns = []
        for w in self._writers:
            for col in w.get_existing_columns():
                if col not in seen:
                    seen.add(col)
                    columns.append(col)
        return columns
