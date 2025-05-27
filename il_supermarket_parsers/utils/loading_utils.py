import re
import os
import datetime
from dataclasses import dataclass
from il_supermarket_scarper import FileTypesFilters
from .logger import Logger

EMPTY_FILE_TOEHOLD = 300


@dataclass
class DumpFile:  # pylint: disable=too-many-instance-attributes
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

    def get_full_path(self):
        """get full file path"""
        return os.path.join(self.store_folder, self.file_name)

    def is_expected_to_be_readable(self):
        """get the file category"""
        return os.path.getsize(self.get_full_path()) == 0

    def is_expected_to_have_records(self):
        """check if the file is expected to have data"""
        return os.path.getsize(self.get_full_path()) > EMPTY_FILE_TOEHOLD

    def to_log_dict(self):
        """return the object as dict"""
        return {
            "store_folder": self.store_folder,
            "file_name": self.file_name,
            "prefix_file_name": self.prefix_file_name,
            "extracted_store_number": self.extracted_store_number,
            "extracted_chain_id": self.extracted_chain_id,
            "extracted_date": self.extracted_date.strftime("%Y-%m-%d %H:%M:%S"),
            "detected_filetype": self.detected_filetype.name,
            "size": os.path.join(self.store_folder, self.file_name),
            "is_expected_to_have_records": self.is_expected_to_have_records(),
        }


def filename_string_to_datetime(date):
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
    index = match.start()
    return (
        FileTypesFilters.get_type_from_file(
            lower_file_name[:index].replace("null", "")
        ),
        lower_file_name[index:],
    )
