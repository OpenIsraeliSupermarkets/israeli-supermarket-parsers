"""Always-running parse worker for queue sources.

One worker per process slot reads a capped inbox fed by
:class:`~il_supermarket_parsers.utils.data_loaders.queue_router.WorkerDispatcher`.
Every (parser, file type) pair is pinned to one worker, so the worker keeps
one open pipeline per pair and closes it when the pair's end marker arrives.
"""

from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from .raw_parsing_pipeline import RawParsingPipeline
from .utils import Logger, create_parser_status, get_output_writer
from .utils.data_loaders.queue_router import (
    MANAGER_CONNECTION_ERRORS,
    QueueManagerConnectionError,
)
from .utils.loading_utils import create_dumpfile_from_queue_message
from .utils.types import OutputConfiguration, StatusConfiguration

PairKey = Tuple[str, str]


def _next_item(inbox: Any, worker_index: int) -> Optional[dict]:
    try:
        return inbox.get()
    except MANAGER_CONNECTION_ERRORS as err:
        Logger.error(
            "Parse worker %d lost its inbox Manager connection: %s", worker_index, err
        )
        raise QueueManagerConnectionError(
            f"Manager connection lost for worker inbox {worker_index}"
        ) from err


class _OpenPair:
    """A pair's pipeline plus how many of its files the worker has taken."""

    def __init__(self, pipeline: RawParsingPipeline):
        self.pipeline = pipeline
        self.files_taken = 0


async def _open_pair(
    key: PairKey,
    output_configuration: List[OutputConfiguration],
    status_configuration: StatusConfiguration,
    limit: Optional[int],
) -> _OpenPair:
    parser_name, file_type = key
    pipeline = RawParsingPipeline(
        data_loader=None,
        output_writer=get_output_writer(parser_name, file_type, output_configuration),
        parser_status=create_parser_status(
            enabled_scraper=parser_name,
            enabled_file_type=file_type,
            status_configuration=status_configuration,
        ),
    )
    await pipeline.start(parser_name, file_type, limit=limit)
    return _OpenPair(pipeline)


async def _close_pair(key: PairKey, pair: _OpenPair, error: Optional[str]) -> None:
    if error:
        Logger.error("Parsing %s/%s ended with error: %s", key[0], key[1], error)
    try:
        pair.pipeline.finish(had_errors=bool(error))
    finally:
        try:
            await pair.pipeline.output_writer.close()
        except (OSError, EOFError, RuntimeError) as err:
            Logger.error("Could not close output for %s/%s: %s", key[0], key[1], err)


async def _parse_file(
    key: PairKey, pair: _OpenPair, message: dict, limit: Optional[int]
) -> None:
    if limit and pair.files_taken >= limit:
        Logger.debug(
            "Limit %s reached for %s/%s, dropping %s",
            limit,
            key[0],
            key[1],
            message.get("file_name"),
        )
        return
    pair.files_taken += 1
    try:
        dump_file = create_dumpfile_from_queue_message(
            file_name=message["file_name"],
            file_content=message["file_content"],
            file_link=message.get("file_link", ""),
            metadata=message.get("metadata", {}),
        )
    except (ValueError, TypeError, AttributeError, KeyError, ValidationError) as err:
        Logger.warning("Skipping queue file %s: %s", message.get("file_name"), err)
        return
    await pair.pipeline.process_file(dump_file)


async def run_queue_worker(
    inbox: Any,
    output_configuration: List[OutputConfiguration],
    status_configuration: StatusConfiguration,
    limit: Optional[int] = None,
    worker_index: int = 0,
) -> None:
    """Parse inbox items until the stop marker (None) arrives.

    A lost inbox connection closes every open pair as failed and re-raises.
    """
    open_pairs: Dict[PairKey, _OpenPair] = {}
    try:
        while True:
            item = _next_item(inbox, worker_index)
            if item is None:
                break
            key = (item["parser_name"], item["file_type"])
            pair = open_pairs.get(key)
            if pair is None:
                pair = await _open_pair(
                    key, output_configuration, status_configuration, limit
                )
                open_pairs[key] = pair

            if item["kind"] == "end":
                del open_pairs[key]
                await _close_pair(key, pair, item.get("error"))
            else:
                await _parse_file(key, pair, item["message"], limit)

    except QueueManagerConnectionError as err:
        for key, pair in list(open_pairs.items()):
            await _close_pair(key, pair, str(err))
        raise

    for key, pair in open_pairs.items():
        await _close_pair(key, pair, "worker stopped before the end of stream")
