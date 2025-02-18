from il_supermarket_parsers import ConvertingTask
from il_supermarket_scarper import ScarpingTask

if __name__ == "__main__":

    ScarpingTask(
        enabled_scrapers=None,
        dump_folder_name="dumps",
        limit=1,  # download one from each
        multiprocessing=None,
        lookup_in_db=True,
    ).start()
    ConvertingTask(
        enabled_parsers=None,
        files_types=None,
        data_folder="dumps",
        multiprocessing=None,
        output_folder="outputs",
    ).start()
