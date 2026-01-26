import asyncio

from il_supermarket_scarper import ScarpingTask, ScraperFactory
from il_supermarket_scarper.utils import _now, Logger
from il_supermarket_parsers import ConvertingTask

Logger.set_logging_level("INFO")


async def main():
    """Main function to run the scraping task and consume results."""
    scraper = ScarpingTask(
        output_configuration={
            "output_mode": "queue",
            "queue_type": "memory",
        },
        status_configuration={"database_type": "json", "base_path": "status_logs"},
        multiprocessing=1,
        enabled_scrapers=[ScraperFactory.BAREKET.name, ScraperFactory.VICTORY.name],
    )

    # Start scraping (runs in background thread)
    scraper.start(limit=1, when_date=_now())

    # Get queue handlers from scraper
    queue_handlers = {
        name: output.queue_handler
        for name, output in scraper.consume().items()
    }

    # Use ConvertingTask with queue and Kafka config
    converter = ConvertingTask(
        enabled_parsers=[ScraperFactory.BAREKET.name, ScraperFactory.VICTORY.name],
        limit=1,
        queue_handlers=queue_handlers,
        kafka_config={
            "bootstrap_servers": ["localhost:9092"],
            "topic": "supermarket-data",
        },
    )

    # Process (sync, but handles async internally via asyncio.run)
    result = converter.start()

    scraper.stop()
    scraper.join()

    print("\nDone!")
    print(f"Processed files: {result}")


if __name__ == "__main__":
    asyncio.run(main())
