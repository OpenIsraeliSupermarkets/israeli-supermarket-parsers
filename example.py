from il_supermarket_parsers import ConvertingTask
from il_supermarket_scarper import ScarpingTask,ScraperFactory
if __name__ == "__main__":



    ScarpingTask(
        enabled_scrapers=[ScraperFactory.BAREKET.name], #download one from each 
        limit=1,
        multiprocessing=2
    ).start()
    scraper = ConvertingTask(
        dump_folder_name="dumps",
        multiprocessing=2
    ).start()