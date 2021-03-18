import asyncio

from aiokafka import AIOKafkaConsumer

from abstractions import TaskProvider


__all__ = ['QueueTaskProvider', 'KafkaTaskProvider']


class QueueTaskProvider(TaskProvider):
    """
    Provides tasks from asyncio.queue. Used by producer
    """
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    async def get(self) -> dict:
        return await self.queue.get()

    def task_done(self):
        self.queue.task_done()


class KafkaTaskProvider(TaskProvider):
    """
    Provides tasks from kafka. Used by consumer
    """
    def __init__(self, consumer: AIOKafkaConsumer):
        self.consumer = consumer

    async def get(self) -> dict:
        return await self.consumer.getone()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.consumer.stop()
