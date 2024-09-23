from il_supermarket_parsers import ConvertingTask
from il_supermarket_scarper import ScarpingTask,ScraperFactory
if __name__ == "__main__":


    multiprocessing = None

    ScarpingTask(
        enabled_scrapers=[ScraperFactory.BAREKET.name], #download one from each 
        dump_folder_name="dumps",
        limit=1,
        multiprocessing=multiprocessing,
        lookup_in_db=True
    ).start()
    scraper = ConvertingTask(
        enabled_parsers=[ScraperFactory.BAREKET.name],
        files_types=None,
        data_folder="dumps",
        multiprocessing=multiprocessing,
        output_folder="outputs"
    ).start()