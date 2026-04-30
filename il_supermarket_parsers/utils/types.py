from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


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
