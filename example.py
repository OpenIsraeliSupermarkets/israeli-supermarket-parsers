from il_supermarket_parsers import ConvertingTask
from il_supermarket_scarper import ScarpingTask
if __name__ == "__main__":

    ScarpingTask(
        enabled_scrapers=None, #download one from each 
        limit=1,
        multiprocessing=2
    )
    scraper = ConvertingTask(
        dump_folder_name="dumps",
        multiprocessing=2
    )
    scraper.start()