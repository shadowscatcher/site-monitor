"""
Creates tables in postgres before starting worker
"""


import argparse
import asyncio
import os

import asyncpg
import loguru

from common.funcs import MissingVariableError
from common.settings import EnvSettings


def configure_parser(parent=None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(parents=[parent] if parent else [], add_help=False)
    parser.add_argument('--scripts', required=True, type=str, help='directory with SQL scripts')
    return parser


async def main(args: argparse.Namespace, settings=EnvSettings()):
    logger = loguru.logger
    with open(os.path.join(args.scripts, 'create.sql')) as fp:
        script = fp.read().strip()

    try:
        conn: asyncpg.Connection = await asyncpg.connect(settings.postgres_dsn)
        await conn.execute(script)
        logger.info('postgres tables initialized')
    except MissingVariableError:  # no postgres dsn available - service don't use postgres
        pass


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main(configure_parser().parse_args()))
