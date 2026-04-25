import abc
import multiprocessing
import queue
import time
from multiprocessing import Queue, current_process
from tqdm import tqdm
from .logger import Logger


def _run_job(job_and_kwargs):
    """Module-level worker function for Pool — must be at module level to be picklable."""
    job_factory, kwargs = job_and_kwargs
    try:
        job_factory().job(**kwargs)
        return {"status": True}
    except Exception as error:  # pylint: disable=broad-except
        Logger.error(f"{current_process().name}: Task failed with {error}")
        return {"status": False, "error": str(error)}


def task(static_job, *arg, **kwarg):
    """execute the job (kept for backward compatibility)"""
    return static_job().processes_job(*arg, **kwarg)


class MultiProcessor:
    """multi processing"""

    def __init__(self, multiprocessing=6):
        self.multiprocessing = multiprocessing
        self.processes = []
        self._pool = None

    def terminate(self):
        """Terminate the worker pool if running."""
        if self._pool is not None:
            self._pool.terminate()

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

    def execute(self, limit=None):
        """execute task"""
        task_args_list = self.get_arguments_list(limit=limit)
        size = len(task_args_list)
        results = []

        if self.multiprocessing:
            job_factory = self.task_to_execute()
            pool_args = [(job_factory, kwargs) for kwargs in task_args_list]

            Logger.info(f"Total Processing... {size} tasks")
            self._pool = multiprocessing.Pool(processes=self.multiprocessing)
            try:
                with tqdm(
                    total=size,
                    desc="Total Processing...",
                    file=Logger.get_stream(),
                ) as pbar:
                    for result in self._pool.imap_unordered(_run_job, pool_args):
                        results.append(result)
                        pbar.update(1)
            finally:
                self._pool.close()
                self._pool.join()
                self._pool = None

        else:
            internal_task = self.task_to_execute()
            tasks_to_accomplish = Queue()
            for kwargs in task_args_list:
                tasks_to_accomplish.put(kwargs)

            while tasks_to_accomplish.qsize() > 0:
                task_kwargs = tasks_to_accomplish.get()
                try:
                    result = internal_task().job(**task_kwargs)
                    results.append({**task_kwargs, "status": True, "response": result})
                except Exception as error:  # pylint: disable=broad-except
                    results.append(
                        {**task_kwargs, "status": False, "error": str(error)}
                    )

        if len(results) != size:
            Logger.warning(
                f"Expected {size} results but got {len(results)}. Some tasks may have failed."
            )
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
        """job to run on process (kept for backward compatibility / direct test use)"""
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

                empty_retry_count = 0
                timeout_retry_count = 0

            except queue.Empty:
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

                time.sleep(1)
                continue

            else:
                try:
                    self.job(**job_kwargs)
                    Logger.info(
                        f"{current_process().name}: Placing results for {job_kwargs}."
                    )

                    put_retry_count = 0
                    max_put_retries = 3
                    while put_retry_count < max_put_retries:
                        try:
                            tasks_accomplished.put(
                                {
                                    **job_kwargs,
                                    "status": True,
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
