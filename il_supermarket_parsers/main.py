from .multiprocess_pharser import ParallelParser
from .utils.logger import Logger


class ConvertingTask:
    """main convert task"""

    def __init__(
        self, data_folder="dumps", number_of_processes=6
    ):
        Logger.info(
            f"Starting Parser, data_folder={data_folder},"
            f"number_of_processes={number_of_processes}"
        )
        self.runner = ParallelParser(
            data_folder,
            number_of_processes=number_of_processes,
        )

    def start(self):
        """run the parsing"""
        return self.runner.execute()
    

if __name__ == "__main__":
    ConvertingTask()
