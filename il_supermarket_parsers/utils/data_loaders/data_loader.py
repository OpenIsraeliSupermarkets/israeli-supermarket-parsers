import os
import asyncio
from typing import AsyncIterator, List, Optional, Set

from il_supermarket_scarper import FileTypesFilters
from il_supermarket_scarper.utils import DumpFolderNames
from ..logger import Logger
from ..loading_utils import DumpFile, file_name_to_components
from .base_data_loader import BaseDataLoader


class DataLoader(BaseDataLoader):
    """class for loading dump files from the folder"""

    def __init__(self, folder: str, empty_store_id: str = "0000") -> None:
        self.folder = folder
        self.empty_store_id = empty_store_id

    async def load(
        self,
        limit: Optional[int] = None,
        enabled_scraper: Optional[list] = None,
        files_types: Optional[list] = None,
    ) -> AsyncIterator[DumpFile]:
        """load details about the files in the folder as async generator"""

        resolved_stores = (
            enabled_scraper if enabled_scraper else DumpFolderNames.all_folders_names()
        )
        resolved_types = files_types if files_types else FileTypesFilters.all_types()
        files_types_set: Set[str] = (
            set(resolved_types)
            if isinstance(resolved_types, list)
            else set(resolved_types)
        )

        files_found = await self._gather_matching_files(
            limit, resolved_stores, files_types_set
        )

        for dump_file in sorted(files_found, key=lambda x: x.extracted_date):
            yield dump_file

    async def _gather_matching_files(
        self,
        limit: Optional[int],
        enabled_scraper: Optional[list],
        files_types_set: Set[str],
    ) -> List[DumpFile]:
        """Scan ``self.folder`` and return matching dump files up to ``limit``."""
        stores_folders = (
            [DumpFolderNames[enum].value for enum in enabled_scraper]
            if enabled_scraper
            else None
        )

        count = 0
        files_found: List[DumpFile] = []

        files_in_dir = await asyncio.to_thread(os.listdir, self.folder)

        for store_name in files_in_dir:
            store_folder = os.path.join(self.folder, store_name)

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
                    f"requested chains to scan {enabled_scraper}"
                )
                continue

            try:
                xml_files = await asyncio.to_thread(os.listdir, store_folder)
            except OSError as err:
                Logger.warning(f"Error listing files in {store_folder}: {err}")
                continue

            for xml in xml_files:
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

        return files_found
