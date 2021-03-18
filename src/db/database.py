import abc
import asyncio
from typing import Any, Union

import asyncpg
import loguru
from dateutil.parser import parse as parse_date


class Repository(metaclass=abc.ABCMeta):
    async def upsert_url(self, url: str) -> int:
        raise NotImplementedError()

    async def save_successful_check(self, data: dict):
        raise NotImplementedError()

    async def save_failed_check(self, data: dict):
        raise NotImplementedError()


class PostgresRepo(Repository):
    def __init__(self, pool_or_dsn: [Union[str, asyncpg.Pool]], logger=loguru.logger, default_timeout_s=10):
        self.pool: asyncpg.Pool = asyncpg.create_pool(pool_or_dsn) if isinstance(pool_or_dsn, str) else pool_or_dsn
        self.logger = logger
        self.default_timeout_s = default_timeout_s
        self.lock = asyncio.Lock()

    async def exec(self, query, *args, timeout=None) -> Any:
        async with self.pool.acquire() as conn:  # type: asyncpg.Connection
            try:
                self.logger.debug('query: {}, args: {}', query, args)
                # result = await conn.execute(query, *args, timeout=timeout or self.default_timeout_s)
                result = await conn.fetch(query, *args, timeout=timeout or self.default_timeout_s)
                self.logger.debug('query result: {}', result)
                return result
            except Exception:
                self.logger.debug('error executing query {} witg args {}', query, args)
                raise

    async def upsert_url(self, url: str) -> int:
        """
        Inserts new url if it not exists in DB

        :param url: unique url
        :return: url id
        """
        # requires postgres >=9.1  https://stackoverflow.com/a/6722460/2465961
        query = """
        WITH new_row AS (
            INSERT INTO sites (url)
            SELECT $1
            WHERE NOT EXISTS(SELECT * FROM sites WHERE url = $1)
            RETURNING id
        )
        SELECT id FROM new_row UNION SELECT id FROM sites WHERE url = $1"""

        async with self.lock:
            records = await self.exec(query, url)
        return records[0]['id']

    async def save_successful_check(self, data: dict):
        """
        :param data: dict with keys url, started, ended, response_time, status
        """
        site_id = await self.upsert_url(data['url'])
        started, ended = parse_date(data['started']), parse_date(data['ended'])
        response_time, status = data['response_time_s'], data['status']
        pattern, match = data.get('pattern'), data.get('match')
        query = 'INSERT INTO success (site_id, started, ended, response_time, status, pattern, match) ' \
                'VALUES ($1, $2, $3, $4, $5, $6, $7)'

        return await self.exec(query, site_id, started, ended, response_time, status, pattern, match)

    async def save_failed_check(self, data: dict):
        """
        :param data: dict with keys url, started, error_type, error
        """
        site_id = await self.upsert_url(data['url'])
        error_type, message = data['error_type'], data['message']
        started = parse_date(data['started'])
        query = 'INSERT INTO errors (site_id, started, error_type, message) VALUES ($1, $2, $3, $4)'
        return await self.exec(query, site_id, started, error_type, message)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.pool.close()
