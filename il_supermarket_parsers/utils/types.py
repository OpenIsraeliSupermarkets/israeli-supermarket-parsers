from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Source configuration
# ---------------------------------------------------------------------------


class FolderSourceConfiguration(BaseModel):
    """Read files from a local directory (default scraper output layout)."""

    folder: str  # default: "dumps"


class QueueSourceConfiguration(BaseModel):
    """Consume files from an in-memory queue produced by a ScarpingTask."""

    queue_handlers: Dict[Any, Any]  # mapping returned by scraper.consume()


SourceConfiguration = Union[FolderSourceConfiguration, QueueSourceConfiguration]


# ---------------------------------------------------------------------------
# Output configurations
# ---------------------------------------------------------------------------


class QueueOutputConfiguration(BaseModel):
    """Write parsed rows into an in-memory queue (consume via converter.consume())."""

    output_mode: Literal["queue"]
    queue_type: Literal["memory"]  # only "memory" is supported; default: "memory"
    queues: Any = None


class CsvOutputConfiguration(BaseModel):
    """Write parsed rows to CSV files on disk."""

    output_mode: Literal["csv"]
    output_folder: str  # directory for output files; default: "outputs"


class KafkaConfig(BaseModel):
    """Connection details for the Kafka output writer."""

    bootstrap_servers: str  # e.g. "localhost:9092"  (required)
    topic_template: str = Field(default="{enabled_scraper}_{enabled_file_type}")


class KafkaOutputConfiguration(BaseModel):
    """Publish parsed rows to a Kafka topic."""

    output_mode: Literal["kafka"]
    kafka_config: KafkaConfig


class MongoConfig(BaseModel):
    """Connection details for the MongoDB output writer."""

    connection_url: str
    db_name: str
    collection_template: str = Field(
        default="{enabled_scraper}_{enabled_file_type}",
    )


class MongoOutputConfiguration(BaseModel):
    """Insert parsed rows into a MongoDB collection."""

    output_mode: Literal["mongo"]
    mongo_config: MongoConfig


OutputConfiguration = Union[
    QueueOutputConfiguration,
    CsvOutputConfiguration,
    KafkaOutputConfiguration,
    MongoOutputConfiguration,
]
"""A single output destination.  Pass a list to fan-out to multiple destinations."""


# ---------------------------------------------------------------------------
# Status / tracking configuration
# ---------------------------------------------------------------------------


class JsonStatusConfiguration(BaseModel):
    """Persist parser status as JSON files on disk."""

    database_type: Literal["json"]  # default when omitted
    base_path: str  # directory for status JSON files; default: "outputs"


class MongoStatusConfiguration(BaseModel):
    """Persist parser status in MongoDB."""

    database_type: Literal["mongo"]
    connection_url: str  # default: "localhost"
    collection_name: str  # default: "scraper_status"
    db_name: str  # MongoDB database name


StatusConfiguration = Union[JsonStatusConfiguration, MongoStatusConfiguration]


class FileCompleteMessage(BaseModel):
    """Message to signal end-of-file with total expected records."""

    file_complete: Literal["true"] = "true"
    file_name: str
    total_expected_records: int


class FileExecutionLog(BaseModel):
    """Log entry for a single file execution"""

    # File information (from DumpFile.to_log_dict())
    store_folder: str
    file_name: str
    prefix_file_name: str
    extracted_store_number: str
    extracted_chain_id: str
    extracted_date: str
    detected_filetype: str
    size: str
    is_expected_to_have_records: bool

    # Execution information
    loaded: bool
    succusfull: Optional[bool] = None
    detected_num_rows: Optional[int] = None
    error: Optional[str] = None
    trace: Optional[str] = None

    def to_dict(self):
        """Convert to dictionary representation (backward compatibility)"""
        return self.dict()


class ExecutionLog(BaseModel):
    """Overall execution log for the pipeline"""

    status: bool
    store_name: str
    files_types: str
    processed_files: bool
    execution_errors: bool
    output_exists: bool
    output_path: Optional[str] = None
    files_to_process: List[str] = Field(default_factory=list)
    execution_log: List[FileExecutionLog] = Field(default_factory=list)

    def to_dict(self):
        """Convert to dictionary representation (backward compatibility)"""
        return self.dict()
