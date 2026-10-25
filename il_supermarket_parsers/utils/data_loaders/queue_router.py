"""Routes scraper queue messages to per-file-type internal queues.

When multiple (chain, file_type) jobs read from the same scraper queue,
the original design had each job put back messages of the wrong type.
This led to race conditions where files were dropped.

This module provides a router that reads each scraper queue once and
dispatches messages to the correct file-type queue based on the detected
file type. Each job then reads only from its own routed queue.
"""

import asyncio
import multiprocessing
import threading
from queue import Empty
from typing import Any, Dict, List, Optional, Set

from pydantic import ValidationError

from ..loading_utils import create_dumpfile_from_queue_message
from ..logger import Logger

# Connection failures raised once the Manager server process is gone.
MANAGER_CONNECTION_ERRORS = (
    EOFError,
    BrokenPipeError,
    ConnectionResetError,
    ConnectionRefusedError,
    ConnectionAbortedError,
)


class QueueManagerConnectionError(RuntimeError):
    """The multiprocessing Manager behind a routed queue is gone."""


class _ManagerHolder:
    """Lazily create one shared multiprocessing.Manager for routed queues."""

    _instance: Any = None

    @classmethod
    def manager(cls) -> Any:
        """Return a shared multiprocessing.Manager (singleton)."""
        if cls._instance is None:
            cls._instance = multiprocessing.Manager()
        return cls._instance


class RoutedQueueHandler:
    """A simple queue handler that wraps a process-safe queue for a single file type.

    This handler is picklable and can be passed to worker processes.
    """

    def __init__(self, internal_queue: Any, scraper_name: str, file_type: str):
        self._queue = internal_queue
        self._scraper_name = scraper_name
        self._file_type = file_type

    async def get_all_messages(self):
        """Yield messages from the routed queue until end-of-stream sentinel."""
        while True:
            try:
                msg = self._queue.get(timeout=0.1)
            except Empty:
                await asyncio.sleep(0.01)
                continue
            except MANAGER_CONNECTION_ERRORS as err:
                Logger.error(
                    "Routed queue %s/%s lost its Manager connection: %s",
                    self._scraper_name,
                    self._file_type,
                    err,
                )
                raise QueueManagerConnectionError(
                    f"Manager connection lost for {self._scraper_name}/{self._file_type}"
                ) from err

            if msg is None:
                return
            yield msg

    async def send(self, msg: dict) -> None:
        """Put a message back - should not be needed with routing."""
        Logger.warning(
            "RoutedQueueHandler.send() called unexpectedly for %s/%s",
            self._scraper_name,
            self._file_type,
        )
        self._queue.put(msg)

    async def close(self) -> None:
        """Re-publish end-of-stream sentinel - not needed for routed queues."""


class RoutedQueueWrapper:
    """Wraps a RoutedQueueHandler to match the scraper queue handler interface.

    This wrapper is picklable and can be passed to worker processes.
    """

    def __init__(self, handler: RoutedQueueHandler):
        self.queue_handler = handler


class QueueRouter:
    """Routes messages from a scraper queue to per-file-type internal queues.

    The router runs in a background thread, reading from the scraper queue
    and dispatching each message to the appropriate file-type queue based
    on the detected file type from the filename.

    Uses process-safe queues (via multiprocessing.Manager) so that the
    routed handlers can be passed to worker processes.
    """

    def __init__(
        self,
        scraper_name: str,
        original_handler: Any,
        enabled_file_types: List[str],
        empty_store_id: str = "0000",
        max_queue_size: int = 0,
    ):
        """Initialize the router.

        Args:
            scraper_name: Name of the scraper/chain
            original_handler: The original scraper queue handler
            enabled_file_types: List of file type names to route
            empty_store_id: Default store ID for files without store number
            max_queue_size: Cap for each routed queue. 0 leaves it unbounded.
                A full queue blocks ``put`` until a consumer takes an item.
        """
        self._scraper_name = scraper_name
        self._original_handler = original_handler
        self._enabled_file_types = set(enabled_file_types)
        self._empty_store_id = empty_store_id
        self._max_queue_size = max_queue_size

        self._routed_queues: Dict[str, Any] = {}
        manager = _ManagerHolder.manager()
        for file_type in enabled_file_types:
            self._routed_queues[file_type] = manager.Queue(max_queue_size)

        self._router_thread: Optional[threading.Thread] = None
        self._started = False
        self._finished = threading.Event()

    def get_routed_handler(self, file_type: str) -> RoutedQueueWrapper:
        """Get the routed queue handler for a specific file type.

        Args:
            file_type: The file type name (e.g. "PRICE_FILE")

        Returns:
            A RoutedQueueWrapper that can be used like the original handler
        """
        if file_type not in self._routed_queues:
            raise ValueError(
                f"File type {file_type} not in enabled types: {self._enabled_file_types}"
            )
        handler = RoutedQueueHandler(
            self._routed_queues[file_type], self._scraper_name, file_type
        )
        return RoutedQueueWrapper(handler)

    def start(self) -> None:
        """Start the routing thread."""
        if self._started:
            return
        self._started = True
        self._router_thread = threading.Thread(
            target=self._run_router,
            name=f"queue-router-{self._scraper_name}",
            daemon=True,
        )
        self._router_thread.start()

    def _run_router(self) -> None:
        """Router thread main loop - reads from scraper queue and dispatches."""
        asyncio.run(self._async_router())

    async def _async_router(self) -> None:
        """Async router implementation."""
        try:
            skipped_types: Set[str] = set()
            async for msg in self._original_handler.queue_handler.get_all_messages():
                file_name = msg.get("file_name", "")
                file_content = msg.get("file_content", b"")
                file_link = msg.get("file_link", "")
                metadata = msg.get("metadata", {})

                try:
                    dump_file = create_dumpfile_from_queue_message(
                        file_name=file_name,
                        file_content=file_content,
                        file_link=file_link,
                        metadata=metadata,
                        empty_store_id=self._empty_store_id,
                    )
                    file_type = dump_file.detected_filetype.name
                except (ValueError, TypeError, AttributeError, ValidationError) as err:
                    Logger.warning("Router skipping queue file %s: %s", file_name, err)
                    continue

                if file_type in self._routed_queues:
                    # Blocks while this file-type queue is full (backpressure).
                    self._put_routed(file_type, msg)
                    Logger.debug(
                        "Routed %s to %s queue for %s",
                        file_name,
                        file_type,
                        self._scraper_name,
                    )
                else:
                    if file_type not in skipped_types:
                        Logger.debug(
                            "Skipping file %s with type %s (not in enabled types %s)",
                            file_name,
                            file_type,
                            self._enabled_file_types,
                        )
                        skipped_types.add(file_type)

            await self._original_handler.queue_handler.close()
            Logger.debug(
                "Re-published end-of-stream sentinel for %s queue",
                self._scraper_name,
            )

        finally:
            for file_type in self._routed_queues:
                # Blocking put: the sentinel waits for a free slot when the
                # queue is full, so it is not dropped ahead of real files.
                self._put_sentinel(file_type)
            self._finished.set()

    def _put_routed(self, file_type: str, msg: dict) -> None:
        """Put one routed file, blocking while that queue is at its cap."""
        try:
            self._routed_queues[file_type].put(msg)
        except MANAGER_CONNECTION_ERRORS as err:
            Logger.error(
                "Queue router %s failed to route %s (%s): %s",
                self._scraper_name,
                msg.get("file_name", ""),
                file_type,
                err,
            )
            raise QueueManagerConnectionError(
                f"Manager connection lost while routing {self._scraper_name}/{file_type}"
            ) from err

    def _put_sentinel(self, file_type: str) -> None:
        """Deliver the end-of-stream marker, including when the queue is full."""
        try:
            self._routed_queues[file_type].put(None)
        except MANAGER_CONNECTION_ERRORS as err:
            Logger.error(
                "Queue router %s could not end %s after Manager failure: %s",
                self._scraper_name,
                file_type,
                err,
            )
        else:
            Logger.debug(
                "Sent end-of-stream to routed queue %s/%s",
                self._scraper_name,
                file_type,
            )

    def wait(self, timeout: Optional[float] = None) -> bool:
        """Wait for the router to finish processing all messages.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if the router finished, False if timeout occurred
        """
        return self._finished.wait(timeout=timeout)


def create_routed_queue_handlers(
    queue_handlers: Dict[str, Any],
    enabled_file_types: List[str],
    max_queue_size: int = 0,
) -> Dict[str, Dict[str, RoutedQueueWrapper]]:
    """Create routed queue handlers for all scrapers.

    Args:
        queue_handlers: Dict mapping scraper names to queue handlers
        enabled_file_types: List of file type names to route
        max_queue_size: Cap for each routed queue. 0 leaves it unbounded.

    Returns:
        Dict mapping scraper names to dicts of (file_type -> RoutedQueueWrapper)
    """
    routers: Dict[str, QueueRouter] = {}
    routed_handlers: Dict[str, Dict[str, RoutedQueueWrapper]] = {}

    for scraper_name, handler in queue_handlers.items():
        router = QueueRouter(
            scraper_name,
            handler,
            enabled_file_types,
            max_queue_size=max_queue_size,
        )
        routers[scraper_name] = router

        routed_handlers[scraper_name] = {}
        for file_type in enabled_file_types:
            routed_handlers[scraper_name][file_type] = router.get_routed_handler(
                file_type
            )

        router.start()

    return routed_handlers
