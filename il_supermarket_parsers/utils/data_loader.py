import os

from typing import List
from il_supermarket_scarper import FileTypesFilters
from il_supermarket_scarper.utils import DumpFolderNames
from .logger import Logger
from .loading_utils import DumpFile, file_name_to_components


class DataLoader:
    """class for loading dump files from the folder"""

    def __init__(
        self, folder, store_names=None, files_types=None, empty_store_id="0000"
    ) -> None:
        self.folder = folder
        self.store_names = (
            store_names if store_names else DumpFolderNames.all_folders_names()
        )
        self.files_types = files_types if files_types else FileTypesFilters.all_types()
        self.empty_store_id = empty_store_id

    def load(self, limit=None):  # pylint: disable=too-many-branches
        """load details about the files in the folder"""
        files_in_dir = os.listdir(self.folder)
        stores_folders = [DumpFolderNames[enum].value for enum in self.store_names]

        files: List[DumpFile] = []
        for store_name in files_in_dir:
            #
            store_folder = os.path.join(self.folder, store_name)

            # ignore list
            if store_name.startswith("."):
                Logger.debug(f"Skipping folder {store_folder} because it contains '.'")
                continue

            if os.path.isfile(store_folder):
                Logger.debug(
                    f"Skipping folder {store_folder} because it contains  is file and not folder"
                )
                continue

            if self.store_names and store_name not in stores_folders:
                Logger.debug(
                    f"Skipping folder {store_folder} because it not in "
                    f"requested chains to scan {self.store_names}"
                )
                continue

            #
            for xml in os.listdir(store_folder):

                # skip files that are not xml
                extension = xml.split(".")[-1]
                if extension != "xml":
                    Logger.warning(f"Skipping file {xml} because it is not xml file")
                    continue

                dump_file: DumpFile = file_name_to_components(
                    store_folder, xml, empty_store_id=self.empty_store_id
                )
                if dump_file.detected_filetype.name in self.files_types:
                    files.append(dump_file)

                if limit and len(files) >= limit:
                    Logger.warning(f"Reached limit of {limit} files, stopping")
                    break

        return sorted(files, key=lambda x: x.extracted_date)
