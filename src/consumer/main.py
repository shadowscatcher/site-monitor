import argparse
import asyncio
from functools import partial

import asyncpg
from aiokafka import ConsumerRecord, AIOKafkaConsumer, TopicPartition

from common.composer import Composer
from common.kafka import create_consumer
from common.serializer import Serde
from common.settings import EnvSettings
from db import PostgresRepo
from impl import KafkaTaskProvider
from impl.worker import DbWriter


def configure_parser(parent=None) -> argparse.ArgumentParser:
    """
    Adds this module subparser arguments to main's parser, if passed
    :param parent: parser from parent module
    :return: subparser
    """
    parser = argparse.ArgumentParser(parents=[parent] if parent else [], add_help=False)
    parser.add_argument('--no-autocommit', action='store_true', default=False, dest='no_autocommit',
                        help='Do not autocommit offset on message fetch')
    return parser


def commit_offset(consumer: AIOKafkaConsumer, msg: ConsumerRecord):
    tp = TopicPartition(msg.topic, msg.partition)
    asyncio.create_task(consumer.commit({tp: msg.offset + 1}))


async def main(args: argparse.Namespace, settings=EnvSettings()):
    consumer = create_consumer(settings, value_deserializer=Serde(settings.message_encoding).deserialize)

    async with asyncpg.create_pool(settings.postgres_dsn) as pg_pool, KafkaTaskProvider(consumer) as kafka_reader:
        await consumer.start()
        await consumer.seek_to_committed()

        repo = PostgresRepo(pg_pool)
        db_writer = DbWriter(repo, settings.kafka_topic_success, settings.kafka_topic_failure)
        if args.no_autocommit:
            db_writer.success_callback = partial(commit_offset, consumer)

        _ = Composer().run(kafka_reader, [db_writer])
        await asyncio.Queue().get()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(
        main(configure_parser().parse_args())
    )
