from il_supermarket_scarper import ScarpingTask, ScraperFactory
from il_supermarket_parsers import ConvertingTask

if __name__ == "__main__":

    ScarpingTask(
        enabled_scrapers=[ScraperFactory.BAREKET.name],  # download one from each
        dump_folder_name="dumps",
        limit=1,
        multiprocessing=None,
        lookup_in_db=True,
    ).start()
    scraper = ConvertingTask(
        enabled_parsers=[ScraperFactory.BAREKET.name],
        files_types=None,
        data_folder="dumps",
        multiprocessing=None,
        output_folder="outputs",
    ).start()
