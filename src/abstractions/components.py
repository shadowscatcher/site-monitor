import abc
from typing import Awaitable, Any

__all__ = ['Scheduler', 'TaskProvider', 'Worker', 'ProviderClosed']


class TaskProvider(metaclass=abc.ABCMeta):
    """
    Provides the task data from any source. There is an in-memory queue and Kafka implementations,
    but we can also implement fetching tasks from external resource or socket, for example
    """

    @abc.abstractmethod
    async def get(self) -> dict:
        """
        :return: Next task
        :raises: ProviderClosed when no more tasks available
        """
        raise NotImplementedError()

    def task_done(self):
        pass


class Worker(metaclass=abc.ABCMeta):
    """
    Some worker that is able to process data asynchronously. Supposed to work as background task
    """
    @abc.abstractmethod
    async def process(self, task: Any) -> Any:
        raise NotImplementedError()


class Scheduler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def schedule(self, async_callback: Awaitable, interval: dict, *args, **kwargs):
        """
        Schedule asynchronous function to be called with given interval

        :param async_callback: function to call
        :param interval: dictionary with interval settings, e.g. {'seconds': 20, 'minutes': 2}
        :param args: function positional arguments
        :param kwargs: function named arguments
        """
        raise NotImplementedError()


class ProviderClosed(Exception):
    """
    Raised when TaskProvider is closed
    """
