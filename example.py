import asyncio
import threading

from il_supermarket_scarper import ScarpingTask, ScraperFactory
from il_supermarket_scarper.utils import _now, Logger
from il_supermarket_parsers import ConvertingTask

Logger.set_logging_level("INFO")


def _consume_parser_queue(parser_name, queue_handler):
    for result in iter(queue_handler.get_queue().get, None):
        print(f"Publishing results for {parser_name}")
        print("Record published: ", result)


async def publish_results(parsers_queue_handlers):
    """Publish results to Kafka, each parser in its own thread."""
    threads = [
        threading.Thread(
            target=_consume_parser_queue,
            args=(parser_name, queue_handler),
            name=f"publisher-{parser_name}",
            daemon=True,
        )
        for parser_name, queue_handler in parsers_queue_handlers.items()
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


async def main():
    """Main function to run the scraping task and consume results."""

    status_configuration = {
        "database_type": "json",
        "base_path": "status_logs",
    }
    
    enabled_scrapers = [ScraperFactory.BAREKET.name, ScraperFactory.VICTORY.name]
    scraper = ScarpingTask(
        output_configuration={
            "output_mode": "queue",
            "queue_type": "memory",
        },
        status_configuration=status_configuration,
        multiprocessing=1,
        enabled_scrapers=enabled_scrapers,
    )

    # Start scraping (runs in background thread)
    scraper.start(limit=1, when_date=_now())
    
    # patch to wait for the queue to be populated
    import time
    time.sleep(10)

    # Use ConvertingTask with queue output mode
    converter = ConvertingTask(
        enabled_parsers=enabled_scrapers,
        limit=1,
        queue_handlers=scraper.consume(),
        output_configuration={
            "output_mode": "queue",
            "queue_type": "memory",
        },
        status_configuration=status_configuration,
    )

    # Grab output queue handles before starting (queues must exist before producers run)
    parsers_queue_handlers = converter.consume()

    # Start converting in background, then consume results
    converter.start(limit=1)
    await publish_results(parsers_queue_handlers)
    converter.join()

    try:
        scraper.stop()
        scraper.join()
    except RuntimeError:
        pass  # Scraper already finished

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
