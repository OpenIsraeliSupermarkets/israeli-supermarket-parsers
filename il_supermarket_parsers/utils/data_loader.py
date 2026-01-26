import os
import asyncio
from typing import AsyncIterator, Optional

from il_supermarket_scarper import FileTypesFilters
from il_supermarket_scarper.utils import DumpFolderNames
from .logger import Logger
from .loading_utils import DumpFile, file_name_to_components
from .base_data_loader import BaseDataLoader


class DataLoader(BaseDataLoader):
    """class for loading dump files from the folder"""

    def __init__(
        self, folder: str, empty_store_id: str = "0000"
    ) -> None:
        self.folder = folder
        self.empty_store_id = empty_store_id

    async def load(
        self, 
        limit: Optional[int] = None, 
        store_names: Optional[list] = None, 
        files_types: Optional[list] = None
    ) -> AsyncIterator[DumpFile]:  # pylint: disable=too-many-branches
        """load details about the files in the folder as async generator"""
        
        store_names = (
            store_names if store_names else DumpFolderNames.all_folders_names()
        )
        files_types = files_types if files_types else FileTypesFilters.all_types()
        files_types_set = set(files_types) if isinstance(files_types, list) else set(files_types)
        
        # Run file system operations in thread pool to avoid blocking
        files_in_dir = await asyncio.to_thread(os.listdir, self.folder)
        stores_folders = [DumpFolderNames[enum].value for enum in store_names] if store_names else None

        count = 0
        files_found = []

        for store_name in files_in_dir:
            store_folder = os.path.join(self.folder, store_name)

            # ignore list
            if store_name.startswith("."):
                Logger.debug(f"Skipping folder {store_folder} because it contains '.'")
                continue

            is_file = await asyncio.to_thread(os.path.isfile, store_folder)
            if is_file:
                Logger.debug(
                    f"Skipping folder {store_folder} because it is file and not folder"
                )
                continue

            if stores_folders and store_name not in stores_folders:
                Logger.debug(
                    f"Skipping folder {store_folder} because it not in "
                    f"requested chains to scan {store_names}"
                )
                continue

            # List files in store folder
            try:
                xml_files = await asyncio.to_thread(os.listdir, store_folder)
            except Exception as e:
                Logger.warning(f"Error listing files in {store_folder}: {e}")
                continue

            for xml in xml_files:
                # skip files that are not xml
                extension = xml.split(".")[-1]
                if extension != "xml":
                    Logger.warning(f"Skipping file {xml} because it is not xml file")
                    continue

                dump_file: DumpFile = file_name_to_components(
                    store_folder, xml, empty_store_id=self.empty_store_id
                )
                
                if dump_file.detected_filetype.name in files_types_set:
                    files_found.append(dump_file)
                    count += 1

                    if limit and count >= limit:
                        Logger.warning(f"Reached limit of {limit} files, stopping")
                        break

            if limit and count >= limit:
                break

        # Sort by date and yield
        for dump_file in sorted(files_found, key=lambda x: x.extracted_date):
            yield dump_file
