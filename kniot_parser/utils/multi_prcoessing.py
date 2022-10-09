import abc
import queue
from multiprocessing import Queue, Process, current_process
from .logger import Logger


class MultiProcessor:
    """multi processing"""

    def __init__(self, task_to_execute, number_of_processes=6):
        self.number_of_processes = number_of_processes
        self.task_to_execute = task_to_execute
        self.processes = []
        self.files_to_process = None

    def start_processes(self, static_job, args):
        """start the number of processers"""
        for index in range(self.number_of_processes):
            processor = Process(target=lambda: static_job().processes_job, args=args)
            self.processes.append(processor)
            processor.start()

            Logger.info(f"Starting process {index}.")

    def wait_to_finish(self):
        """wait until all finish"""
        Logger.info("Starting waiting to all processes")
        for pool in self.processes:
            pool.join()

        Logger.info("Finished waiting to all processes")

    @abc.abstractmethod
    def get_arguments_list(self):
        """create list of arguments"""
        raise NotImplementedError()

    def get_tasks_queue(
        self,
    ):
        """get a queue with all the tasks need to execute"""

        task_can_executed_indepentlly = self.get_arguments_list()
        tasks_to_accomplish = Queue()
        for raw in task_can_executed_indepentlly:
            tasks_to_accomplish.put(*raw)

        return tasks_to_accomplish

    def execute(self):
        """execute task"""
        tasks_to_accomplish = self.get_tasks_queue()
        tasks_accomplish = Queue()

        self.start_processes(
            self.task_to_execute,
            (
                tasks_to_accomplish,
                tasks_accomplish,
            ),
        )

        self.wait_to_finish()

        results = []
        for task_accomplish in tasks_accomplish:
            file_to_delete = task_accomplish.get_nowait()
            results.append(file_to_delete)

        return results


class ProcessJob:
    """processes jobs"""

    @abc.abstractmethod
    def job(self, **kwargs):
        """the job the process need to run"""
        raise NotImplementedError()

    def processes_job(self, tasks_to_accomplish, tasks_accomplish):
        """job to run on process"""
        while True:
            try:
                task_kwargs = tasks_to_accomplish.get_nowait()
                Logger.info(f"{current_process().name}: Start processing {task_kwargs}")
            except queue.Empty:
                # other-wise the process exits at the start.
                if tasks_to_accomplish.empty():
                    Logger.info(f"{current_process().name}: Queue is empty. existing.")
                    break
            else:
                file_processed = self.job()
                tasks_accomplish.put(file_processed)
                Logger.info(f"{current_process().name}: End processing {task_kwargs}.")
        return True
