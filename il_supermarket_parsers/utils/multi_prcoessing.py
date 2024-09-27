import abc
import time
import queue
from multiprocessing import Queue, Process, current_process
from .logger import Logger


def task(static_job, *arg, **kwarg):
    """execute the job"""
    return static_job().processes_job(*arg, **kwarg)


class MultiProcessor:
    """multi processing"""

    def __init__(self, multiprocessing=6):
        self.multiprocessing = multiprocessing
        self.processes = []
        self.files_to_process = None

    def start_processes(self, static_job, *arg, **kwargs):
        """start the number of processers"""

        if self.multiprocessing:
            for index in range(self.multiprocessing):
                processor = Process(
                    name=f"Process {index}",
                    target=task,
                    args=tuple([static_job] + list(arg)),
                    kwargs=kwargs,
                )
                self.processes.append(processor)

            for processor in self.processes:
                processor.start()

            Logger.info(f"Starting process {index}.")

    def wait_to_finish(self, tasks_accomplished):
        """wait until all finish"""

        if self.multiprocessing:
            Logger.info("Starting waiting to all processes")
            while not tasks_accomplished.full():
                time.sleep(2)

        Logger.info("Finished waiting to all processes")

    @abc.abstractmethod
    def task_to_execute(self):
        """the task to execute"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_arguments_list(self):
        """create list of arguments"""
        raise NotImplementedError()

    def post(self, results):
        """post process the results"""
        return results

    def get_tasks_queue(
        self,
    ):
        """get a queue with all the tasks need to execute"""

        task_can_executed_indepentlly = self.get_arguments_list()
        tasks_to_accomplish = Queue()
        for raw in task_can_executed_indepentlly:
            tasks_to_accomplish.put(raw)
        return tasks_to_accomplish, len(task_can_executed_indepentlly)

    def execute(self):
        """execute task"""
        tasks_to_accomplish, size = self.get_tasks_queue()
        results = []

        if self.multiprocessing:
            tasks_accomplished = Queue(maxsize=size)

            self.start_processes(
                self.task_to_execute(),
                tasks_to_accomplish=tasks_to_accomplish,
                tasks_accomplished=tasks_accomplished,
            )

            # no more jobs
            tasks_to_accomplish.close()
            tasks_to_accomplish.join_thread()

            while not tasks_accomplished.empty() or len(results) < size:
                output = tasks_accomplished.get(True)
                results.append(output)

        else:
            internal_task = self.task_to_execute()
            while tasks_to_accomplish.qsize() > 0:  # or 'while' instead of 'if'
                results.append(internal_task().job(**tasks_to_accomplish.get()))

        assert len(results) == size, f"{len(results)} vs {size}"

        return self.post(results)


class ProcessJob:
    """processes jobs"""

    @abc.abstractmethod
    def job(self, **kwargs):
        """the job the process need to run"""
        raise NotImplementedError()

    def processes_job(self, tasks_to_accomplish=None, tasks_accomplished=None):
        """job to run on process"""
        while True:
            try:
                Logger.info(f"{current_process().name}: Waiting on queue.")
                task_kwargs = tasks_to_accomplish.get(True, timeout=5)
                Logger.info(f"{current_process().name}: Start processing {task_kwargs}")

            except queue.Empty:
                # other-wise the process exits at the start.
                if tasks_to_accomplish.empty():
                    Logger.info(f"{current_process().name}: Queue is empty. existing.")
                    break
            else:

                try:
                    file_processed = self.job(**task_kwargs)
                    Logger.info(
                        f"{current_process().name}: Placing results for {task_kwargs}."
                    )
                    tasks_accomplished.put(
                        {**task_kwargs, "status": False, "response": file_processed},
                        timeout=5,
                    )
                    Logger.info(
                        f"{current_process().name}: End processing {task_kwargs}."
                    )
                except Exception as error:  # pylint: disable=broad-exception-caught
                    Logger.info(
                        f"{current_process().name}:  failed with {error}, exiting."
                    )
                    tasks_accomplished.put({**task_kwargs, "status": False}, timeout=5)
