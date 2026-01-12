import json
from typing import List
import pandas as pd
from kafka import KafkaProducer
from .base_output_writer import BaseOutputWriter
from .logger import Logger


class KafkaOutputWriter(BaseOutputWriter):
    """Kafka output writer with column alignment"""

    def __init__(
        self,
        bootstrap_servers: List[str],
        topic: str,
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
        self.topic = topic
        self.key_columns = key_columns or []
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: (
                json.dumps(k, default=str).encode("utf-8") if k is not None else None
            ),
        )
        self._existing_columns: List[str] = []

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

    def write_batch(self, df: pd.DataFrame) -> None:
        """
        Write a DataFrame batch to Kafka (one row per message) with column alignment

        Args:
            df: DataFrame to write
        """
        if not self.exists():
            Logger.debug(f"Creating new Kafka output for topic {self.topic}")
            self._existing_columns = list(df.columns)
        else:
            Logger.debug(f"Kafka output exists, processing batch")
            # Update existing columns with any new ones from this batch
            self._update_existing_columns(list(df.columns))

            # If there are missing columns in the DataFrame, add them
            missing_columns = set(self._existing_columns) - set(df.columns)
            for column in missing_columns:
                df[column] = None

        # Align columns to match existing schema
        df_aligned = df[self._existing_columns]

        # Send each row as a separate Kafka message
        for _, row in df_aligned.iterrows():
            # Create message value (row as dict)
            value = row.to_dict()

            # Create message key if key_columns specified
            key = None
            if self.key_columns:
                key = {col: row[col] for col in self.key_columns if col in row}

            # Send message
            future = self.producer.send(self.topic, value=value, key=key)
            try:
                future.get(timeout=10)  # Wait for message to be sent
            except Exception as e:
                Logger.error(f"Error sending message to Kafka: {e}")
                raise

        Logger.debug(f"Sent {len(df_aligned)} messages to Kafka topic {self.topic}")

    def close(self) -> None:
        """Close the Kafka producer"""
        self.producer.close()
