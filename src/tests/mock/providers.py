from abstractions import TaskProvider
from abstractions.components import ProviderClosed


__all__ = ['MockProvider']


class MockProvider(TaskProvider):
    def __init__(self, task: dict):
        self.task = task
        self.enabled = True

    async def get(self) -> dict:
        if not self.enabled:
            raise ProviderClosed('out of tasks')

        self.enabled = False
        return self.task
