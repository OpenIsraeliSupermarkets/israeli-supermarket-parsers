from .multiprocess_pharser import ParallelParser
from .utils.logger import Logger


class ConvertingTask:
    """main convert task"""

    def __call__(
        self, data_folder="dumps", number_of_processes=6
    ):
        Logger.info(
            f"Starting Parser, data_folder={data_folder},"
            f"number_of_processes={number_of_processes}"
        )
        files_parsed = ParallelParser(
            data_folder,
            number_of_processes=number_of_processes,
        ).execute()
        Logger.info(f"Ending Parser, files_parsed={files_parsed}")
        return files_parsed


if __name__ == "__main__":
    ConvertingTask()
