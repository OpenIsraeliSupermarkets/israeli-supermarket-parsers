import os
import re
import datetime
from dataclasses import dataclass
from il_supermarket_scarper import FileTypesFilters
from il_supermarket_scarper.utils import DumpFolderNames
from .logger import Logger


@dataclass
class DumpFile:  # pylint: disable=too-many-instance-attributes
    """information about file found from the scraper"""

    store_folder: str
    file_name: str
    prefix_file_name: str
    extracted_store_number: str
    extracted_chain_id: str
    extracted_date: datetime.datetime
    detected_filetype: str
    data: str = None

    def get_full_path(self):
        """get full file path"""
        return os.path.join(self.store_folder, self.file_name)


class DataLoader:
    """class for loading dump files from the folder"""

    def __init__(
        self, folder, store_names=None, files_types=None, empty_store_id=0000
    ) -> None:
        self.folder = folder
        self.store_names = store_names
        self.files_types = files_types
        self.empty_store_id = empty_store_id

    def _format_datetime(self, date):
        """format the datetime"""
        if len(date) == 12:
            # if doesn't include seconds
            return datetime.datetime.strptime(date, "%Y%m%d%H%M")
        if len(date) == 14:
            # if include seconds
            return datetime.datetime.strptime(date, "%Y%m%d%H%M%S")
        raise ValueError(f"'{date}' format doesn't match any.")

    def _file_name_to_components(self, store_folder, file_name, empty_store_id="0000"):
        """extract file name components"""
        try:
            prefix_file_name, store_number, date, *_ = file_name.split(".")[0].split(
                "-"
            )
        except ValueError:
            # global files
            prefix_file_name, date, *_ = file_name.split(".")[0].split("-")
            store_number = empty_store_id

        file_type, chain_id = self._find_file_type_and_chain_id(prefix_file_name)

        return DumpFile(
            file_name=file_name,
            store_folder=store_folder,
            prefix_file_name=prefix_file_name,
            extracted_store_number=store_number,
            extracted_chain_id=chain_id,
            extracted_date=self._format_datetime(date),
            detected_filetype=file_type,
        )

    @classmethod
    def _find_file_type_and_chain_id(cls, file_name):
        """get the file type"""
        lower_file_name = file_name.lower()
        match = re.search(r"\d", lower_file_name)
        index = match.start()
        return (
            FileTypesFilters.get_type_from_file(lower_file_name[:index]),
            lower_file_name[index:],
        )

    def load(self):
        """load details about the files in the folder"""
        files_in_dir = os.listdir(self.folder)
        stores_folders = [DumpFolderNames[enum].value for enum in self.store_names]

        files = []
        for store_name in files_in_dir:
            #
            store_folder = os.path.join(self.folder, store_name)

            # ignore list
            ignore_reason = None
            if store_name.startswith("."):
                ignore_reason = " contains '.'"
            if os.path.isfile(store_folder):
                ignore_reason = "is file and not folder"
            if self.store_names and store_name not in stores_folders:
                ignore_reason = "not in requested chains to scan"

            if ignore_reason:
                Logger.warning(f"Ignoreing file {store_folder}, {ignore_reason}")
                continue
            #
            for xml in os.listdir(store_folder):

                # skip files that are not xml
                ignore_file_reseaon = ""
                extension = xml.split(".")[-1]
                if extension != "xml":
                    ignore_file_reseaon = (
                        ignore_file_reseaon + f"file type not in {extension}"
                    )
                if "null" in xml.lower():
                    ignore_file_reseaon = ignore_file_reseaon + " null file "

                if os.path.getsize(os.path.join(store_folder, xml)) == 0:
                    ignore_file_reseaon = "file is empty."

                if len(ignore_file_reseaon) > 0:
                    Logger.warning(
                        f"Ignoreing file {store_folder}, {ignore_file_reseaon}."
                    )
                    continue

                files.append(
                    self._file_name_to_components(
                        store_folder, xml, empty_store_id=self.empty_store_id
                    )
                )
        return sorted(files, key=lambda x: x.extracted_date)
