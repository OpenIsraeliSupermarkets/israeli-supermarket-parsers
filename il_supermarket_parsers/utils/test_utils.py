import datetime
import shutil
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from il_supermarket_scarper import ScarpingTask, FileTypesFilters, ScraperFactory
from il_supermarket_scarper.utils import _now

from il_supermarket_parsers.task import ConvertingTask


@dataclass
class SampleDataOptions:
    """Optional parameters for :func:`get_sample_data`."""

    filter_type: Optional[Any] = None
    enabled_scrapers: Optional[List[str]] = None
    limit: int = None
    queue_handlers: Optional[Dict[str, Any]] = None
    kafka_config: Optional[Dict[str, Any]] = None
    use_streaming: bool = False


def get_sample_data(dump_folder_name: str, options: Optional[SampleDataOptions] = None):
    """
    Get data to scrape and optionally process it.

    Args:
        dump_folder_name: Folder name to download files to (for file mode,
            ignored in streaming mode)
        options: Optional flags; defaults are all unset/off.

    Returns:
        For streaming mode (queue_handlers provided or use_streaming=True):
            Result from ConvertingTask.
        For file mode: dump_folder_name
    """

    status_folder = os.path.join(dump_folder_name, "status_logs")

    if os.path.isdir(status_folder):
        shutil.rmtree(status_folder)

    o = options or SampleDataOptions()

    # Streaming mode: use queue-based scraping and processing
    if o.queue_handlers is not None or o.use_streaming:
        scraper = None
        queue_handlers = o.queue_handlers
        if queue_handlers is None:
            scraper = ScarpingTask(
                output_configuration={
                    "output_mode": "queue",
                    "queue_type": "memory",
                },
                status_configuration={
                    "database_type": "json",
                    "base_path": status_folder,
                },
                multiprocessing=1,
                enabled_scrapers=o.enabled_scrapers if o.enabled_scrapers else None,
                files_types=[o.filter_type] if o.filter_type else None,
            )

            scraper.start(limit=o.limit, when_date=_now())

            queue_handlers = {
                name: output.queue_handler for name, output in scraper.consume().items()
            }

        output_cfg = {}
        if o.kafka_config:
            output_cfg["kafka_config"] = o.kafka_config

        converter = ConvertingTask(
            enabled_parsers=o.enabled_scrapers if o.enabled_scrapers else None,
            files_types=[o.filter_type] if o.filter_type else None,
            limit=o.limit,
            source_configuration={"queue_handlers": queue_handlers},
            output_configuration=output_cfg or None,
        )

        result = converter.start()

        if scraper is not None:
            scraper.stop()
            scraper.join()

        return result

    task = ScarpingTask(
        output_configuration={
            "output_mode": "disk",
            "base_storage_path": dump_folder_name,
        },
        status_configuration={"database_type": "json", "base_path": "status_logs"},
        multiprocessing=1,
        enabled_scrapers=o.enabled_scrapers if o.enabled_scrapers else None,
        files_types=[o.filter_type] if o.filter_type else None,
    )
    task.start(
        limit=o.limit,
        when_date=datetime.datetime.now() if o.filter_type else None,
    )
    task.join()
    return dump_folder_name


def get_sample_store_data():
    """get only store to scrape"""
    return


def get_sample_price_data():
    """get only price to scrape"""
    return get_sample_data(
        "samples_price",
        SampleDataOptions(filter_type=FileTypesFilters.PRICE_FILE.name),
    )


def get_sample_price_full_data():
    """get only price full to scrape"""
    return get_sample_data(
        "samples_price_full",
        SampleDataOptions(filter_type=FileTypesFilters.PRICE_FULL_FILE.name),
    )


def get_sample_promo_data():
    """get only promo to scrape"""
    return get_sample_data(
        "samples_promo",
        SampleDataOptions(filter_type=FileTypesFilters.PROMO_FILE.name),
    )


def get_sample_promo_full_data():
    """get only promo full to scrape"""
    return get_sample_data(
        "samples_promo_full",
        SampleDataOptions(filter_type=FileTypesFilters.PROMO_FULL_FILE.name),
    )


def get_all_chain_ids():
    """get all chain ids"""
    all_ids = []
    for chain_constractor in ScraperFactory.all_scrapers():
        all_ids.extend(chain_constractor().get_chain_id())
    return all_ids


def get_all_scrapers_names():
    """get all chain ids"""
    all_names = []
    for chain_constractor in ScraperFactory.all_scrapers():
        all_names.append(chain_constractor.__name__)
    return all_names
