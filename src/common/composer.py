import asyncio
from typing import List

import loguru

from abstractions import TaskProvider, Worker, ProviderClosed
from impl import QueueTaskProvider


class Composer:
    """
    Composer creates and starts a pipeline of workers in background
    """
    def __init__(self, logger=None):
        self.logger = logger or loguru.logger

    def run(self, task_provider: TaskProvider, processors: List[Worker], output_handlers: List[Worker] = None) -> \
            List[asyncio.Task]:
        """
        Creates pipeline with workers and queues between them and schedules it in running lopp

        :param task_provider: Entity that creates initial tasks, like URL query scheduler or kafka consumer
        :param processors: Workers that process initial tasks and produce a results
        :param output_handlers: Optional processors for results (Kafka publisher for producer)
        :return:
        """
        if output_handlers:
            results_queue = asyncio.Queue()
            tasks = run_workers(task_provider, processors, results_queue, self.logger)
            tasks.extend(run_workers(QueueTaskProvider(results_queue), output_handlers, logger=self.logger))
            self.logger.info('started {} processor(s) and {} publisher(s)', len(processors), len(output_handlers))
            return tasks

        processor_tasks = run_workers(task_provider, processors, logger=self.logger)
        self.logger.info('started {} processor(s)', len(processors))
        return processor_tasks


async def process_tasks(provider: TaskProvider, worker: Worker, output_queue: asyncio.Queue = None,
                        logger=loguru.logger):
    """
    Background worker caller
    """
    while True:
        try:
            task = await provider.get()
            logger.debug('sending task to worker: {} - {}', worker.__class__.__name__, task)
            result = await worker.process(task)
            logger.debug('worker {} returned {}', worker.__class__.__name__, result)
            if output_queue and result:
                await output_queue.put(result)
        except ProviderClosed:
            return
        finally:
            provider.task_done()


def run_workers(task_provider: TaskProvider, workers: List[Worker],
                output_queue: asyncio.Queue = None, logger=loguru.logger) -> List[asyncio.Task]:
    """
    Schedules tasks in the currently running event loop
    """
    return [asyncio.create_task(process_tasks(task_provider, worker, output_queue, logger)) for worker in workers]
