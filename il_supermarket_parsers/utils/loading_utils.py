import re
import os
import datetime
from typing import Optional

from pydantic import BaseModel
from il_supermarket_scarper import FileTypesFilters

from .logger import Logger

EMPTY_FILE_TOEHOLD = 300
_NON_DUMP_EXTENSIONS = frozenset({"json", "csv", "txt", "log", "md", "py", "pyc"})


class DumpFile(BaseModel):  # pylint: disable=too-many-instance-attributes
    """information about file found from the scraper"""

    store_folder: str
    file_name: str
    prefix_file_name: str
    extracted_store_number: str
    extracted_chain_id: str
    extracted_date: datetime.datetime
    detected_filetype: FileTypesFilters
    data: str = None
    #
    should_be_processed: bool = True
    ingore_reason: str = None
    # Queue-based file support
    file_content: Optional[bytes] = None
    file_link: Optional[str] = None

    @property
    def get_full_path(self) -> str:
        """get full file path"""
        return os.path.join(self.store_folder, self.file_name)

    @property
    def is_expected_to_be_readable(self) -> bool:
        """Returns True if the file has content and can be parsed."""
        if self.file_content is not None:
            return len(self.file_content) > 0
        if os.path.exists(self.get_full_path):
            return os.path.getsize(self.get_full_path) > 0
        return False

    @property
    def is_expected_to_have_records(self) -> bool:
        """check if the file is expected to have data"""
        # If file_content is provided (queue-based), check content length
        if self.file_content is not None:
            return len(self.file_content) > EMPTY_FILE_TOEHOLD
        # Otherwise check file system
        if os.path.exists(self.get_full_path):
            return os.path.getsize(self.get_full_path) > EMPTY_FILE_TOEHOLD
        return False

    @property
    def is_queue_based(self) -> bool:
        """check if file is from queue (in-memory)"""
        return self.file_content is not None


def is_dump_file_name(file_name: str) -> bool:
    """True if this looks like a supermarket dump rather than a sidecar file.

    Daily-publish and several chains persist dumps as ``.xml``, ``.gz``,
    ``.xml.gz``, or with no extension at all. Sidecars (``.json`` status,
    ``.csv`` outputs, etc.) must stay ignored.
    """
    base = os.path.basename(file_name)
    if not base or base.startswith("."):
        return False
    if "." in base:
        extension = base.rsplit(".", 1)[-1].lower()
        if extension in _NON_DUMP_EXTENSIONS:
            return False
    return True


def filename_string_to_datetime(date) -> datetime.datetime:
    """format the datetime"""
    if len(date) == 8:
        # if doesn't include seconds
        return datetime.datetime.strptime(date, "%Y%m%d")
    if len(date) == 12:
        # if doesn't include seconds
        return datetime.datetime.strptime(date, "%Y%m%d%H%M")
    if len(date) == 14:
        # if include seconds
        return datetime.datetime.strptime(date, "%Y%m%d%H%M%S")
    raise ValueError(f"'{date}' format doesn't match any.")


def file_name_to_components(store_folder, file_name, empty_store_id="0000"):
    """extract file name components"""

    _file_name_split = file_name.split(".")[0].split("-")
    try:
        # Promo7290700100008-000-207-20250224-103225
        if len(_file_name_split) == 5:
            prefix_file_name, _, store_number, date, time, *_ = _file_name_split
            extracted_datetime = date + time
        else:
            prefix_file_name, store_number, extracted_datetime, *_ = _file_name_split
    except ValueError:
        Logger.warning(f"Error parsing file name {file_name}")

        # global files
        prefix_file_name, extracted_datetime, *_ = _file_name_split
        store_number = empty_store_id

    file_type, chain_id = filename_to_file_type_and_chain_id(prefix_file_name)

    return DumpFile(
        file_name=file_name,
        store_folder=store_folder,
        prefix_file_name=prefix_file_name,
        extracted_store_number=store_number,
        extracted_chain_id=chain_id,
        extracted_date=filename_string_to_datetime(extracted_datetime),
        detected_filetype=file_type,
    )


def filename_to_file_type_and_chain_id(file_name):
    """get the file type"""
    lower_file_name = file_name.lower()
    match = re.search(r"\d", lower_file_name)
    if match is None:
        raise ValueError(f"No chain id in file name {file_name}")
    index = match.start()
    file_type = FileTypesFilters.get_type_from_file(
        lower_file_name[:index].replace("null", "")
    )
    if file_type is None:
        raise ValueError(f"Unknown file type in file name {file_name}")
    return file_type, lower_file_name[index:]


def create_dumpfile_from_queue_message(
    file_name: str,
    file_content: bytes,
    file_link: str,
    metadata: dict,
    empty_store_id: str = "0000",
) -> DumpFile:
    """Create DumpFile from queue message"""
    # Extract components from file name
    _file_name_split = file_name.split(".")[0].split("-")
    try:
        # Promo7290700100008-000-207-20250224-103225
        if len(_file_name_split) == 5:
            prefix_file_name, _, store_number, date, time, *_ = _file_name_split
            extracted_datetime = date + time
        else:
            prefix_file_name, store_number, extracted_datetime, *_ = _file_name_split
    except ValueError:
        Logger.warning(f"Error parsing file name {file_name}")
        # global files
        prefix_file_name, extracted_datetime, *_ = _file_name_split
        store_number = empty_store_id

    file_type, chain_id = filename_to_file_type_and_chain_id(prefix_file_name)

    # Use metadata or file_name to determine store_folder
    # For queue-based files, store_folder might be a virtual path
    store_folder = metadata.get("store_folder", f"queue/{chain_id}")

    return DumpFile(
        file_name=file_name,
        store_folder=store_folder,
        prefix_file_name=prefix_file_name,
        extracted_store_number=store_number,
        extracted_chain_id=chain_id,
        extracted_date=filename_string_to_datetime(extracted_datetime),
        detected_filetype=file_type,
        file_content=file_content,
        file_link=file_link,
    )
