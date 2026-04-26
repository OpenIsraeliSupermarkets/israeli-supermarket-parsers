from typing import AsyncIterator, Optional
from .base_data_loader import BaseDataLoader
from ..loading_utils import DumpFile, create_dumpfile_from_queue_message
from ..logger import Logger


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

    def queue_count(self) -> int:
        """Return the number of scraper queues connected to this loader."""
        return len(self.queue_handlers)

    async def load(
        self,
        limit: Optional[int] = None,
        enabled_scraper: Optional[list] = None,
        files_types: Optional[list] = None,
    ) -> AsyncIterator[DumpFile]:
        """
        Load dump files from queues as async generator

        Args:
            limit: Optional limit on number of files to load
            enabled_scraper: Optional list of store names to filter
            files_types: Optional list of file types to filter

        Yields:
            DumpFile objects as they arrive from queues
        """
        count = 0
        for scraper_name, queue_handler in self.queue_handlers.items():
            # Only consume from queues matching the requested store names
            if enabled_scraper and scraper_name not in enabled_scraper:
                continue

            Logger.debug(f"Consuming files from {scraper_name} queue")

            try:
                already_rejected = set()
                async for msg in queue_handler.queue_handler.get_all_messages():
                    file_name = msg["file_name"]
                    file_content = msg["file_content"]
                    file_link = msg.get("file_link", "")
                    metadata = msg.get("metadata", {})

                    dump_file: DumpFile = create_dumpfile_from_queue_message(
                        file_name=file_name,
                        file_content=file_content,
                        file_link=file_link,
                        metadata=metadata,
                        empty_store_id=self.empty_store_id,
                    )

                    if (
                        files_types
                        and dump_file.detected_filetype.name not in files_types
                    ):
                        if file_name in already_rejected:
                            Logger.warning(
                                f"File {file_name} was already put back once and returned to this consumer — "
                                f"no other consumer is handling type {dump_file.detected_filetype}. Skipping."
                            )
                            continue
                        Logger.debug(
                            f"Skipping file {file_name} (type {dump_file.detected_filetype} not in {files_types}), putting back for another consumer"
                        )
                        already_rejected.add(file_name)
                        await queue_handler.queue_handler.send(msg)
                        continue

                    Logger.debug(
                        f"Yielding dump file: {dump_file.file_name} from {scraper_name} queue"
                    )
                    yield dump_file
                    count += 1

                    if limit and count >= limit:
                        Logger.info(f"Reached limit of {limit} files, stopping")
                        return

                # The sentinel (None) was consumed by this process. Re-publish it so
                # other concurrent consumers of the same queue can also terminate.
                await queue_handler.queue_handler.close()
                Logger.debug(
                    f"Re-published end-of-stream sentinel for {scraper_name} queue"
                )

            except Exception as e:
                Logger.error(f"Error consuming from {scraper_name} queue: {e}")
                raise

        Logger.info(
            f"Finished consuming {enabled_scraper} with {files_types} {count} files from queues"
        )
