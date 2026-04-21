import asyncio

from il_supermarket_scarper import ScarpingTask, ScraperFactory
from il_supermarket_scarper.utils import _now, Logger
from il_supermarket_parsers import ConvertingTask

Logger.set_logging_level("INFO")


async def publish_results(parsers_queue_handlers):
    """Publish results to Kafka"""
    for parser_name, queue_handler in parsers_queue_handlers.items():
        while True:
            print(f"Publishing results for {parser_name}")
            result = queue_handler.get()
            if result is None:
                break
            print("Record published: ", result)


async def main():
    """Main function to run the scraping task and consume results."""

    enabled_scrapers = [ScraperFactory.BAREKET.name, ScraperFactory.VICTORY.name]
    scraper = ScarpingTask(
        output_configuration={
            "output_mode": "queue",
            "queue_type": "memory",
        },
        status_configuration={"database_type": "json", "base_path": "status_logs"},
        multiprocessing=1,
        enabled_scrapers=enabled_scrapers,
    )

    # Start scraping (runs in background thread)
    scraper.start(limit=1, when_date=_now())

    # Get queue handlers from scraper
    queue_handlers = {
        name: output.queue_handler for name, output in scraper.consume().items()
    }

    # Use ConvertingTask with queue and Kafka config
    converter = ConvertingTask(
        enabled_parsers=enabled_scrapers,
        limit=1,
        queue_handlers=queue_handlers,
        output_configuration={
            "output_mode": "queue",
            "queue_type": "memory",
        },
        status_configuration={"database_type": "json", "base_path": "status_logs"},
    )

    parsers_queue_handlers = {
        name: output.queue_handler for name, output in converter.consume().items()
    }

    # Process (sync, but handles async internally via asyncio.run)
    result = converter.start()

    await publish_results(parsers_queue_handlers)

    try:
        scraper.stop()
        scraper.join()
    except RuntimeError:
        pass  # Scraper already finished

    print("\nDone!")
    print(f"Processed files: {result}")


if __name__ == "__main__":
    asyncio.run(main())
