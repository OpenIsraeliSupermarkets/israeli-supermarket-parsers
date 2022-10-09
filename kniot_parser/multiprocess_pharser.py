from .convert import XmlToDataBaseConverter
from .utils.multi_prcoessing import MultiProcessor, ProcessJob
from .utils.data_loading import read_dump_folder
from .utils.logger import Logger



class ConvertingProcess(ProcessJob):
    """converting file to database"""

    def job(self, **kwargs):
        """read the dump folder and filter according to the requested filters
        start processing file according to thier "update_date"
        """
        # take args
        data_folder  = kwargs.pop("data_folder")
        filter_task_kwargs = kwargs.pop("filter_task_kwargs")

        def insert_task(
            full_path, file_type, update_date, branch_store_id, store_name, **_
        ):
            """insert files into database"""
            return XmlToDataBaseConverter(branch_store_id, store_name).convert(
                full_path, file_type, update_date
            )

        files = read_dump_folder(data_folder)
        # select only the files selected by the filter
        Logger.info(f"When loading the data saw {files.shape[0]} files.")
        for key in filter_task_kwargs:
            files = files[filter_task_kwargs[key] == files[key]]
            Logger.info(
                f"When filltering using {key} the data saw {files.shape[0]} files"
            )
        # make sure they are inserted in order
        files = files.sort_values("update_date")
        file_processed = list()
        for _, line in files.iterrows():
            # the processing should be execute by order
            # if the inserter fails, stop processing.
            if not insert_task(**line):
                return False

            file_processed.append(line)

        return file_processed


class ParallelParser(MultiProcessor):
    """run insert task on parallel"""

    def __init__(self, data_folder, folder_to_process=None, number_of_processes=6):
        super().__init__(
            task_to_execute=ConvertingProcess, number_of_processes=number_of_processes
        )
        self.data_folder = data_folder
        self.folder_to_process = folder_to_process

    def get_arguments_list(self):
        """create list of arguments"""
        # task_can_executed_indepentlly = list(
        #     files_data_frame.groupby(columns_kwarg).groups
        # )
        task_groups = ["store_name", "branch_store_id", "file_type"]
        files_data_frame = self.get_args_data_frame()
        task_can_executed_indepentlly = list(files_data_frame[task_groups].unqiue())
        return task_can_executed_indepentlly

    def get_args_data_frame(self):
        """get the data frame"""
        data_frame = read_dump_folder(self.data_folder)
        if self.folder_to_process:
            data_frame = data_frame[
                data_frame["store_name"].isin(self.folder_to_process)
            ]
        return data_frame
