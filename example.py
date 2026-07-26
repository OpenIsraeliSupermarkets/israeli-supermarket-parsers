import asyncio
import threading

from il_supermarket_scarper import ScarpingTask, ScraperFactory
from il_supermarket_scarper.utils import _now, Logger
from il_supermarket_parsers import ConvertingTask

Logger.set_logging_level("INFO")


def _consume_parser_queue(scraper, file_type, queue_handler):
    count = 0
    for result in queue_handler.get_all_messages():
        print(f"Publishing results for {scraper} / {file_type}")
        print("Record published: ", result)

        if "total_expected_records" in result:
            if result["total_expected_records"] == count:
                break
            print(
                f"Expected {result['total_expected_records']} records, but got {count}"
            )
            break
        count += 1
    print(f"Finished consuming {count} records from {scraper} / {file_type}")


async def publish_results(parsers_queue_handlers):
    """Publish results to Kafka, each (scraper, file_type) in its own thread."""
    threads = [
        threading.Thread(
            target=_consume_parser_queue,
            args=(scraper, file_type, queue_handler),
            name=f"publisher-{scraper}-{file_type}",
            daemon=True,
        )
        for (scraper, file_type), queue_handler in parsers_queue_handlers.items()
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

    enabled_scrapers = [
        ScraperFactory.VICTORY_NEW_SOURCE.name,
        ScraperFactory.YELLOW.name,
    ]
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

    # Use ConvertingTask with queue output mode
    converter = ConvertingTask(
        enabled_parsers=enabled_scrapers,
        source_configuration={"queue_handlers": scraper.consume()},
        output_configuration=[
            {
                "output_mode": "queue",
                "queue_type": "memory",
            },
            {
                "output_mode": "csv",
                "output_folder": "outputs",
            },
        ],
        status_configuration=status_configuration,
    )

    # Grab output queue handles before starting (queues must exist before producers run)
    parsers_queue_handlers = converter.consume()

    # Start converting in background, then consume results
    converter.start()

    # print things as they come in
    await publish_results(parsers_queue_handlers)

    try:
        scraper.stop()
        scraper.join()
    except (RuntimeError, OSError, FileNotFoundError, AttributeError):
        # Manager/socket may be gone if scraper already shut down or after pool fork.
        pass

    try:
        converter.join()
    except RuntimeError:
        pass  # Converter already finished

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
