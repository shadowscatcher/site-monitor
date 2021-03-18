import asyncio
from datetime import datetime
from typing import Any, Callable, Awaitable

import loguru
from dateutil.relativedelta import relativedelta

from abstractions import Scheduler

__all__ = ['SimpleScheduler']


class SimpleScheduler(Scheduler):
    """
    Schedules a callback with given interval
    """
    def __init__(self, logger=loguru.logger):
        self.logger = logger

    def schedule(self, async_callback: Callable[[Any], Awaitable[str]], interval: dict, *args, **kwargs):
        """
        :param async_callback: Function to call to call
        :param interval: dateutil.relativedelta constructor arguments
        :param args: function args
        :param kwargs: function kwargs
        :return:
        """
        asyncio.create_task(self.loop(async_callback, interval, *args, **kwargs))

    @loguru.logger.catch
    async def loop(self, async_callback, interval_kwargs, *args, **kwargs):
        async def callback():
            self.logger.debug('calling callback function')
            await async_callback(*args, **kwargs)

        previous_call = datetime.now()
        await callback()

        while True:
            next_call = previous_call + relativedelta(**interval_kwargs)
            previous_call = next_call
            now = datetime.now()

            if next_call < now:
                continue

            pause = (next_call - now).total_seconds()
            await asyncio.sleep(pause)
            await callback()
