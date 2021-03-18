from db import Repository


class MockRepository(Repository):
    def __init__(self):
        self.success = []
        self.fail = []

    async def upsert_url(self, url: str) -> int:
        pass

    async def save_successful_check(self, data: dict):
        self.success.append(data)

    async def save_failed_check(self, data: dict):
        self.fail.append(data)
