import threading
from concurrent.futures import ProcessPoolExecutor


class RalphPoolExecutor(ProcessPoolExecutor):
    """
    A class with a customized version of the `ProcessPoolExecutor`,
    to get more information on the status of the current workers.
    Modified with the help of Stack Overflow and Claude.ai.

    :param max_workers: A maximum number of workers.
    :type max_workers: int

    :param log: logger object where Controller logs are stored.
    :type log: logging.Logger

    Additional arguments:
    self._lock: a threading.Lock() is necessary to prevent submit()
        and _worker_is_done() functions to call from different threads.
    """
    def __init__(self, max_workers=None, logger=None, *args, **kwargs):
        super().__init__(max_workers, *args, **kwargs)
        self.max_workers = max_workers
        self.log = logger
        self._lock = threading.Lock()
        self._running_workers = 0
        self._completed = 0
        self._submitted = 0

    def submit(self, fn, *args, **kwargs):
        """
        A function that submits a new worker. Inherit the majority of its
        functionality from `concurrent.futures.Executor.submit()` method,
        and adds more information about what is happening to the logs (when a worker starts
        and ends its job). As per `concurrent.futures.Executor documentation
        <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Executor.submit>`:
        it schedules a callable (`fn`) to be executed as a function with `*args` and `**kwargs`.
        It returns a `Future` object representing the execution of the callable `fn`.

        :param fn: A callable to be executed as a function with `*args` and `**kwargs`.
        :type fn: callable

        :return: A `Future` object representing the execution of the callable `fn`.
        :rtype: `concurrent.futures.Future`
        """
        future = super().submit(fn, *args, **kwargs)
        with self._lock:
            self._running_workers += 1
            self._submitted += 1
            usage, submitted = self._running_workers, self._submitted

        if self.log:
            self.log.info(
                f"Controller: deployed worker for "
                f"{self._describe(args)}. "
                f"Active: {usage}/{self.max_workers} "
                f"(submitted so far: {submitted})"
            )

        future.add_done_callback(lambda f: self._worker_is_done(f, args))
        return future

    def _worker_is_done(self, future, args):
        """
        A method invoked, when a worker ended its job.
        It updates the information on the currently running workers,
        and ones that completed their job, and then logs the information.

        :param future: A `Future` object representing the execution of the callable `fn`.
        :type future: concurrent.futures.Future

        :param args: A list of arguments to be passed to the callable `fn`.
        :type args: list
        """
        with self._lock:
            self._running_workers -= 1
            self._completed += 1
            usage, completed, submitted = (
                self._running_workers, self._completed, self._submitted,
            )

        if self.log:
            if future.exception():
                self.log.error(
                    f"Controller: worker FAILED on {self._describe(args)}: "
                    f"{future.exception()}"
                )
            else:
                self.log.info(
                    f"Controller: worker finished {self._describe(args)}. "
                    f"Active: {usage}/{self.max_workers} "
                    f"(completed: {completed}/{submitted})"
                )

    def get_pool_usage(self):
        """
        A method that checks how many workers are running at the time,
        under a lock, so that callers from any thread can get consistent
        information.
        """
        with self._lock:
            return self._running_workers

    @staticmethod
    def _describe(args):
        """
        A method that builds a human-readable label for a task submitted to the executor,
        to be used in log messages.

        If the first positional argument looks like a command list containing the
        ``--event_name`` flag (as constructed by :meth:`Controller.launch_analysts`),
        the corresponding event name is extracted and returned. Otherwise, falls back
        to a raw representation of ``args``.

        :param args: The positional arguments that were passed to :meth:`submit`,
            i.e. the arguments forwarded to the submitted function.
        :type args: tuple

        :return: A short, human-readable description of the task, e.g. ``"event 'event_42'"``
            or ``"task (['python', ...],)"`` as a fallback.
        :rtype: str
        """
        if args and isinstance(args[0], list) and "--event_name" in args[0]:
            command = args[0]
            idx = command.index("--event_name")
            try:
                return f"event '{command[idx + 1]}'"
            except IndexError:
                pass
        return f"task {args!r}"