import asyncio
from datetime import timezone, datetime
from typing import Any

import loguru

from abstractions import Worker

__all__ = ['MockPublisher', 'MockSitePoller']


class MockPublisher(Worker):
    def __init__(self, queue: asyncio.Queue, logger=loguru.logger):
        self.queue = queue
        self.logger = logger

    async def process(self, task: dict) -> Any:
        self.logger.debug('publisher task: {}', task)
        await self.queue.put(task)


class MockSitePoller(Worker):
    def __init__(self, logger=loguru.logger):
        self.logger = logger

    async def process(self, task: dict) -> Any:
        self.logger.debug('quering task: {}', task)
        started = datetime.now(timezone.utc).astimezone()
        # await asyncio.sleep(random())
        ended = datetime.now(timezone.utc).astimezone()

        return {
            'url': task.get('url'),
            'status': 200,
            'text': '<head></head><body><stomack><beer>0.5 litres</beer></stomack></body>',
            'pattern': 'litres',
            'match': True,
            'started': started,
            'ended': ended,
            'elapsed': ended - started,
        }
