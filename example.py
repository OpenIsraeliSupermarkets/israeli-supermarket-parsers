from il_supermarket_parsers import ConvertingTask
from il_supermarket_scarper import ScarpingTask,ScraperFactory
if __name__ == "__main__":


    multiprocessing = None

    ScarpingTask(
        enabled_scrapers=[ScraperFactory.BAREKET.name], #download one from each 
        limit=1,
        multiprocessing=multiprocessing,
        lookup_in_db=True
    ).start()
    scraper = ConvertingTask(
        data_folder="dumps",
        multiprocessing=multiprocessing
    ).start()