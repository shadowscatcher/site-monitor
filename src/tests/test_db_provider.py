import asyncio
import random
import string
from typing import NamedTuple

import asyncpg
import pytest

from common.settings import EnvSettings
from db import PostgresRepo


@pytest.fixture
def conn_pool():
    loop = asyncio.get_event_loop()
    settings = EnvSettings()
    pool = loop.run_until_complete(asyncpg.create_pool(settings.postgres_dsn))
    yield pool
    loop.run_until_complete(pool.close())


@pytest.fixture
def db_repo(conn_pool) -> PostgresRepo:
    return PostgresRepo(conn_pool)


def random_string() -> str:
    return ''.join([random.choice(string.ascii_letters) for _ in range(20)])


class MockRecord(NamedTuple):
    topic: str
    value: dict


async def get_records(pool: asyncpg.Pool, url: str):
    async with pool.acquire() as conn:
        records_success = await conn.fetch(
            'SELECT * FROM success JOIN sites s on s.id = success.site_id WHERE url = $1', url)
        records_fail = await conn.fetch(
            'SELECT * FROM errors JOIN sites s on s.id = errors.site_id WHERE url = $1', url)
        return records_success, records_fail


@pytest.mark.integration
def test_pg_repo_upsert(db_repo):
    loop = asyncio.get_event_loop()

    random_url1, random_url2 = random_string(), random_string()

    site_id = loop.run_until_complete(db_repo.upsert_url(random_url1))
    assert site_id, 'first site entry not created'

    site_id_2 = loop.run_until_complete(db_repo.upsert_url(random_url1))
    assert site_id_2 == site_id, 'same URL inserted twice'

    site_id_3 = loop.run_until_complete(db_repo.upsert_url(random_url2))
    assert site_id_3 != site_id, 'same id returned for different urls'


@pytest.mark.integration
def test_pg_insert_success(db_repo, conn_pool):
    # arrange
    random_url = random_string()
    loop = asyncio.get_event_loop()
    success_report = {'started': '2021-03-16T19:58:53.450004+00:00', 'ended': '2021-03-16T19:58:54.374555+00:00',
                      'response_time_s': 0.924551, 'status': 200, 'success': True, 'url': random_url,
                      'match': True, 'pattern': 'Ongoing incident'}
    fail_report = {
        'started': '2021-03-16T21:30:03.058589+00:00', 'success': False,
        'error_type': "<class 'aiohttp.client_exceptions.ClientConnectorError'>",
        'message': f'Cannot connect to host {random_url}:443 ssl:default [Name or service not known]',
        'url': random_url}

    tasks = [
        db_repo.save_successful_check(success_report),
        db_repo.save_failed_check(fail_report)
    ]

    # act
    loop.run_until_complete(asyncio.gather(*tasks))
    records_success, records_fail = loop.run_until_complete(get_records(conn_pool, random_url))

    # assert
    assert records_success
    assert records_fail
    sr, fr = records_success[0], records_fail[0]

    assert sr['site_id'] == fr['site_id'], 'site id mismatch'
    assert sr['started'] != fr['started']
