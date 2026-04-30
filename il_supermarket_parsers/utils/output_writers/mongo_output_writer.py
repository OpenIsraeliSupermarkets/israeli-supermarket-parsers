import asyncio
from typing import List

from pymongo import MongoClient

from .base_output_writer import BaseOutputWriter
from ..logger import Logger
from ..loading_utils import DumpFile


class MongoOutputWriter(BaseOutputWriter):
    """MongoDB output writer with column alignment (same rules as Kafka writer)."""

    def __init__(
        self,
        connection_url: str,
        db_name: str,
        collection_name: str,
    ):
        self.connection_url = connection_url
        self.db_name = db_name
        self.collection_name = collection_name
        self._client = MongoClient(connection_url)
        self._collection = self._client[db_name][collection_name]
        self._existing_columns: List[str] = []
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        Logger.debug(
            f"Initialized Mongo output writer for {self.db_name}.{self.collection_name}"
        )

    async def initialize_new_file(self, file: DumpFile) -> None:
        self._existing_columns = []
        Logger.debug(
            f"Reset Mongo output columns for {self.db_name}.{self.collection_name}"
        )

    def exists(self) -> bool:
        return len(self._existing_columns) > 0

    def get_path(self) -> str:
        return f"mongodb:///{self.db_name}/{self.collection_name}"

    def get_existing_columns(self) -> List[str]:
        return self._existing_columns.copy()

    def _update_existing_columns(self, new_columns: List[str]) -> None:
        all_columns = set(self._existing_columns) | set(new_columns)
        self._existing_columns = sorted(list(all_columns))

    async def write_row(self, row: dict) -> None:
        if not self._initialized:
            await self.initialize()

        row_columns = list(row.keys())
        if not self.exists():
            Logger.debug(
                f"Creating new Mongo output for {self.db_name}.{self.collection_name}"
            )
            self._existing_columns = row_columns
        else:
            self._update_existing_columns(row_columns)

        aligned_row = {}
        for col in self._existing_columns:
            aligned_row[col] = row.get(col, None)

        def _insert():
            self._collection.insert_one(aligned_row)

        await asyncio.to_thread(_insert)

    async def close(self) -> None:
        await asyncio.to_thread(self._client.close)
