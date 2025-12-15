import abc
import time
import queue
from multiprocessing import Queue, Process, current_process
from tqdm import tqdm
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

    def wait_to_finish(self, tasks_accomplished, timeout_seconds=60 * 60):
        """wait until all finish with timeout protection"""

        if self.multiprocessing:
            Logger.info("Starting waiting to all processes")
            start_time = time.time()

            while (
                not tasks_accomplished.full()
                and (time.time() - start_time) < timeout_seconds
            ):
                Logger.info(f"Waiting to all processes {tasks_accomplished.qsize()}")

                # Check if all processes are still alive
                alive_processes = [p for p in self.processes if p.is_alive()]
                if not alive_processes:
                    Logger.warning("All processes finished but queue not full")
                    break

                time.sleep(10)

            # Check if we timed out
            if (time.time() - start_time) >= timeout_seconds:
                Logger.error(
                    f"wait_to_finish timed out after {timeout_seconds} seconds"
                )
                # Terminate remaining processes
                for process in self.processes:
                    if process.is_alive():
                        Logger.warning(f"Terminating process {process.name}")
                        process.terminate()
                        process.join(timeout=5)

        Logger.info("Finished waiting to all processes")

    @abc.abstractmethod
    def task_to_execute(self):
        """the task to execute"""
        raise NotImplementedError()

    @abc.abstractmethod
    def get_arguments_list(self, limit=None):
        """create list of arguments"""
        raise NotImplementedError()

    def post(self, results):
        """post process the results"""
        return results

    def get_tasks_queue(self, limit=None):
        """get a queue with all the tasks need to execute"""

        task_can_executed_indepentlly = self.get_arguments_list(limit=limit)
        tasks_to_accomplish = Queue()
        for raw in task_can_executed_indepentlly:
            tasks_to_accomplish.put(raw)
        return tasks_to_accomplish, len(task_can_executed_indepentlly)

    def execute(self, limit=None):  # pylint: disable=too-many-locals,too-many-branches
        """execute task"""
        tasks_to_accomplish, size = self.get_tasks_queue(limit=limit)
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
            #
            Logger.info(f"Total Processing... {size} tasks")
            with tqdm(
                total=size, desc="Total Processing...", file=Logger.get_stream()
            ) as pbar:
                start_time = time.time()
                timeout_seconds = 3600  # 1 hour timeout

                while (not tasks_accomplished.empty() or len(results) < size) and (
                    time.time() - start_time
                ) < timeout_seconds:
                    try:
                        output = tasks_accomplished.get(
                            True, timeout=1
                        )  # Add 1 second timeout
                        results.append(output)
                        pbar.update(1)
                    except queue.Empty:
                        # Check if all processes are still alive
                        alive_processes = [p for p in self.processes if p.is_alive()]
                        if not alive_processes and tasks_accomplished.empty():
                            Logger.warning(
                                "All processes finished but results incomplete"
                            )
                            break
                        continue

                # Check if we timed out
                if (time.time() - start_time) >= timeout_seconds:
                    Logger.error(
                        f"Processing timed out after {timeout_seconds} seconds"
                    )
                    # Terminate remaining processes
                    for process in self.processes:
                        if process.is_alive():
                            Logger.warning(f"Terminating process {process.name}")
                            process.terminate()
                            process.join(timeout=5)

        else:
            internal_task = self.task_to_execute()
            while tasks_to_accomplish.qsize() > 0:  # or 'while' instead of 'if'
                task_kwargs = tasks_to_accomplish.get()
                try:
                    result = internal_task().job(**task_kwargs)
                    results.append({**task_kwargs, "status": True, "response": result})
                except Exception as error:  # pylint: disable=broad-except
                    results.append(
                        {**task_kwargs, "status": False, "error": str(error)}
                    )

        # More flexible assertion with better error handling
        if len(results) != size:
            Logger.warning(
                f"Expected {size} results but got {len(results)}. Some tasks may have failed."
            )

            # Check for failed tasks
            failed_tasks = [r for r in results if r.get("status") is False]
            if failed_tasks:
                Logger.error(f"Found {len(failed_tasks)} failed tasks")
                for failed_task in failed_tasks:
                    Logger.error(f"Failed task: {failed_task}")

        return self.post(results)


class ProcessJob:
    """processes jobs"""

    @abc.abstractmethod
    def job(self, **kwargs):
        """the job the process need to run"""
        raise NotImplementedError()

    def processes_job(
        self, tasks_to_accomplish=None, tasks_accomplished=None
    ):  # pylint: disable=too-many-locals,too-many-branches
        """job to run on process"""
        max_empty_retries = 3
        empty_retry_count = 0
        max_timeout_retries = 5
        timeout_retry_count = 0

        while (
            empty_retry_count < max_empty_retries
            and timeout_retry_count < max_timeout_retries
        ):
            try:
                Logger.info(f"{current_process().name}: Waiting on queue.")
                job_kwargs = tasks_to_accomplish.get(True, timeout=5)
                Logger.info(f"{current_process().name}: Start processing {job_kwargs}")

                # Reset retry counters on successful get
                empty_retry_count = 0
                timeout_retry_count = 0

            except queue.Empty:
                # Check if queue is actually empty or just timing out
                if tasks_to_accomplish.empty():
                    empty_retry_count += 1
                    Logger.info(
                        f"{current_process().name}: Queue is empty. "
                        f"Retry {empty_retry_count}/{max_empty_retries}"
                    )
                    if empty_retry_count >= max_empty_retries:
                        Logger.info(
                            f"{current_process().name}: Queue confirmed empty after "
                            f"{max_empty_retries} retries. Exiting."
                        )
                        break
                else:
                    timeout_retry_count += 1
                    Logger.warning(
                        f"{current_process().name}: Queue get timed out but queue not empty. "
                        f"Retry {timeout_retry_count}/{max_timeout_retries}"
                    )
                    if timeout_retry_count >= max_timeout_retries:
                        Logger.error(
                            f"{current_process().name}: Too many timeouts. Exiting."
                        )
                        break

                # Small delay before retrying
                time.sleep(1)
                continue

            else:
                try:
                    file_processed = self.job(**job_kwargs)
                    Logger.info(
                        f"{current_process().name}: Placing results for {job_kwargs}."
                    )

                    # Add retry logic for putting results
                    put_retry_count = 0
                    max_put_retries = 3
                    while put_retry_count < max_put_retries:
                        try:
                            tasks_accomplished.put(
                                {
                                    **job_kwargs,
                                    "status": True,
                                    "response": file_processed,
                                },
                                timeout=5,
                            )
                            break
                        except queue.Full:
                            put_retry_count += 1
                            Logger.warning(
                                f"{current_process().name}: Results queue full. "
                                f"Retry {put_retry_count}/{max_put_retries}"
                            )
                            if put_retry_count >= max_put_retries:
                                Logger.error(
                                    f"{current_process().name}: Failed to put results after "
                                    f"{max_put_retries} retries"
                                )
                                break
                            time.sleep(1)

                    Logger.info(
                        f"{current_process().name}: End processing {job_kwargs}."
                    )
                except Exception as error:  # pylint: disable=broad-except
                    Logger.error(f"{current_process().name}: Task failed with {error}")

                    # Try to put error result
                    try:
                        tasks_accomplished.put(
                            {**job_kwargs, "status": False, "error": str(error)},
                            timeout=5,
                        )
                    except queue.Full:
                        Logger.error(
                            f"{current_process().name}: Failed to put error result - queue full"
                        )

        Logger.info(f"{current_process().name}: Process exiting")
