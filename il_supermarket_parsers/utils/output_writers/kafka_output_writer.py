import json
import asyncio
from typing import List, Optional
from kafka import KafkaProducer
from .base_output_writer import BaseOutputWriter
from ..logger import Logger


class KafkaOutputWriter(BaseOutputWriter):
    """Kafka output writer with column alignment"""

    def __init__(
        self,
        bootstrap_servers: List[str],
        enabled_scraper: str,
        enabled_file_type: str,
        key_columns: List[str] = None,
    ):
        """
        Initialize Kafka output writer

        Args:
            bootstrap_servers: List of Kafka broker addresses
            topic: Kafka topic name
            key_columns: Optional list of column names to use as message key
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = f"{enabled_scraper}_{enabled_file_type}".lower()
        self.key_columns = key_columns or []
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: (
                json.dumps(k, default=str).encode("utf-8") if k is not None else None
            ),
        )
        self._existing_columns: List[str] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the output writer"""
        self._initialized = True
        Logger.debug(f"Initialized Kafka output writer for topic {self.topic}")

    def exists(self) -> bool:
        """Check if output exists (for Kafka, checks if columns are known)"""
        return len(self._existing_columns) > 0

    def get_path(self) -> str:
        """Get the Kafka topic identifier"""
        return f"kafka://{','.join(self.bootstrap_servers)}/{self.topic}"

    def get_existing_columns(self) -> List[str]:
        """Get existing columns for alignment"""
        return self._existing_columns.copy()

    def _update_existing_columns(self, new_columns: List[str]) -> None:
        """Update the set of existing columns"""
        all_columns = set(self._existing_columns) | set(new_columns)
        self._existing_columns = sorted(list(all_columns))

    async def write_row(self, row: dict) -> None:
        """
        Write a single row to Kafka with column alignment

        Args:
            row: Dictionary representing a single row
        """
        if not self._initialized:
            await self.initialize()

        # Update existing columns with any new ones from this row
        row_columns = list(row.keys())
        if not self.exists():
            Logger.debug(f"Creating new Kafka output for topic {self.topic}")
            self._existing_columns = row_columns
        else:
            self._update_existing_columns(row_columns)

        # Align row to match existing schema (add None for missing columns)
        aligned_row = {}
        for col in self._existing_columns:
            aligned_row[col] = row.get(col, None)

        # Create message value
        value = aligned_row

        # Create message key if key_columns specified
        key = None
        if self.key_columns:
            key = {
                col: aligned_row[col] for col in self.key_columns if col in aligned_row
            }

        # Send message (run in thread pool to avoid blocking)
        def _send_message():
            future = self.producer.send(self.topic, value=value, key=key)
            try:
                future.get(timeout=10)  # Wait for message to be sent
            except Exception as e:
                Logger.error(f"Error sending message to Kafka: {e}")
                raise

        await asyncio.to_thread(_send_message)

    def close(self) -> None:
        """Close the Kafka producer"""
        self.producer.close()
