import datetime
from il_supermarket_scarper import ScarpingTask, FileTypesFilters, ScraperFactory
from il_supermarket_scarper.utils import _now
from il_supermarket_parsers.task import ConvertingTask


def get_sample_data(
    dump_folder_name,
    filter_type=None,
    enabled_scrapers=None,
    limit=3,
    queue_handlers=None,
    kafka_config=None,
    use_streaming=False,
):
    """
    Get data to scrape and optionally process it.
    
    Args:
        dump_folder_name: Folder name to download files to (for file mode, ignored in streaming mode)
        filter_type: Optional file type filter
        enabled_scrapers: Optional list of scraper names to enable
        limit: Limit on number of files to scrape
        queue_handlers: Optional dict of queue handlers (if provided, uses streaming mode)
        kafka_config: Optional dict with Kafka config for streaming mode
            - bootstrap_servers: List of Kafka broker addresses
            - topic: Kafka topic name
            - key_columns: Optional list of column names for message key
        use_streaming: If True and queue_handlers not provided, set up scraper with queue output
    
    Returns:
        - For streaming mode (queue_handlers provided or use_streaming=True): Result from ConvertingTask
        - For file mode: dump_folder_name
    """
    # Streaming mode: use queue-based scraping and processing
    if queue_handlers is not None or use_streaming:
        # If queue_handlers not provided but use_streaming=True, set up scraper
        scraper = None
        if queue_handlers is None:
            # Set up scraper with queue output
            scraper = ScarpingTask(
                output_configuration={
                    "output_mode": "queue",
                    "queue_type": "memory",
                },
                status_configuration={"database_type": "json", "base_path": "status_logs"},
                multiprocessing=1,
                enabled_scrapers=enabled_scrapers if enabled_scrapers else None,
                files_types=[filter_type] if filter_type else None,
                suppress_exception=True,
            )
            
            # Start scraping (runs in background thread)
            scraper.start(limit=limit, when_date=_now())
            
            # Get queue handlers from scraper
            queue_handlers = {
                name: output.queue_handler
                for name, output in scraper.consume().items()
            }
        
        # Create ConvertingTask with queue and Kafka config
        converter = ConvertingTask(
            enabled_parsers=enabled_scrapers if enabled_scrapers else None,
            files_types=[filter_type] if filter_type else None,
            limit=limit,
            queue_handlers=queue_handlers,
            kafka_config=kafka_config,
        )
        
        # Process and return result
        result = converter.start()
        
        # Cleanup scraper if we created it
        if scraper is not None:
            scraper.stop()
            scraper.join()
        
        return result
    
    # File mode: traditional scraping to disk
    if filter_type:
        task = ScarpingTask(
            dump_folder_name=dump_folder_name,
            limit=limit,
            files_types=[filter_type],
            enabled_scrapers=enabled_scrapers if enabled_scrapers else None,
            lookup_in_db=False,
            when_date=datetime.datetime.now(),  # get from today, some site remove old files
            suppress_exception=True,
        )
        task.start()
    else:
        ScarpingTask(
            dump_folder_name=dump_folder_name, limit=limit, lookup_in_db=True
        ).start()
    return dump_folder_name


def get_sample_store_data():
    """get only store to scrape"""
    return


def get_sample_price_data():
    """get only price to scrape"""
    return get_sample_data("samples_price", FileTypesFilters.PRICE_FILE.name)


def get_sample_price_full_data():
    """get only price full to scrape"""
    return get_sample_data("samples_price_full", FileTypesFilters.PRICE_FULL_FILE.name)


def get_sample_promo_data():
    """get only promo to scrape"""
    return get_sample_data("samples_promo", FileTypesFilters.PROMO_FILE.name)


def get_sample_promo_full_data():
    """get only promo full to scrape"""
    return get_sample_data("samples_promo_full", FileTypesFilters.PROMO_FULL_FILE.name)


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


# def get_scraper_name_from_id(chain_id):
#     """get the constractor name from the chain id"""
#     for chain_constractor in ScraperFactory.all_scrapers():
#         if str(chain_id) in (chain_constractor().get_chain_id()):
#             return chain_constractor.__name__
#     raise ValueError(f"chain_id {chain_id} is not recognized ")
