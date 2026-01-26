from typing import AsyncIterator, Optional
from il_supermarket_scarper import FileTypesFilters
from .base_data_loader import BaseDataLoader
from .loading_utils import DumpFile, create_dumpfile_from_queue_message
from .logger import Logger


class QueueDataLoader(BaseDataLoader):
    """Data loader for consuming files from scraper queues"""

    def __init__(self, queue_handlers: dict, empty_store_id: str = "0000"):
        """
        Initialize QueueDataLoader

        Args:
            queue_handlers: Dict mapping scraper names to queue handler objects
                          Each handler should have get_all_messages() async generator
            empty_store_id: Default store ID for files without store number
        """
        self.queue_handlers = queue_handlers
        self.empty_store_id = empty_store_id

    async def load(
        self,
        limit: Optional[int] = None,
        store_names: Optional[list] = None,
        files_types: Optional[list] = None,
    ) -> AsyncIterator[DumpFile]:
        """
        Load dump files from queues as async generator

        Args:
            limit: Optional limit on number of files to load
            store_names: Optional list of store names to filter (not used for queues)
            files_types: Optional list of file types to filter

        Yields:
            DumpFile objects as they arrive from queues
        """
        files_types = files_types if files_types else FileTypesFilters.all_types()
        files_types_set = set(files_types) if isinstance(files_types, list) else set(files_types)

        count = 0
        for scraper_name, queue_handler in self.queue_handlers.items():
            Logger.debug(f"Consuming files from {scraper_name} queue")
            
            try:
                async for msg in queue_handler.get_all_messages():
                    file_name = msg["file_name"]
                    file_content = msg["file_content"]
                    file_link = msg.get("file_link", "")
                    metadata = msg.get("metadata", {})

                    # Create DumpFile from queue message
                    dump_file = create_dumpfile_from_queue_message(
                        file_name=file_name,
                        file_content=file_content,
                        file_link=file_link,
                        metadata=metadata,
                        empty_store_id=self.empty_store_id,
                    )

                    # Filter by file type if specified
                    if dump_file.detected_filetype.name not in files_types_set:
                        Logger.debug(
                            f"Skipping file {file_name} - file type {dump_file.detected_filetype.name} "
                            f"not in requested types {files_types}"
                        )
                        continue

                    yield dump_file
                    count += 1

                    if limit and count >= limit:
                        Logger.info(f"Reached limit of {limit} files, stopping")
                        return

            except Exception as e:
                Logger.error(f"Error consuming from {scraper_name} queue: {e}")
                raise

        Logger.info(f"Finished consuming {count} files from queues")
