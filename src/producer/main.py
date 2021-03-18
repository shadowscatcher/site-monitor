import argparse
import asyncio
import os

from loguru import logger
import yaml

from abstractions.components import Scheduler
from common.composer import Composer
from common.kafka import create_producer
from common.serializer import Serde
from common.settings import EnvSettings
from impl import SimpleScheduler, QueueTaskProvider, KafkaPublisher, AsyncSitePoller



def configure_parser(parent=None) -> argparse.ArgumentParser:
    """
    Adds this module subparser arguments to main's parser, if passed
    :param parent: parser from parent module
    :return: subparser
    """
    parent = argparse.ArgumentParser(parents=[parent] if parent else [], add_help=False)
    parent.add_argument('--targets-file', help='path to file with target sites', type=str)
    parent.add_argument('--url', help='site to check')
    parent.add_argument('--seconds', default=60, help='polling interval in seconds', type=int)
    parent.add_argument('--pattern', help='pattern to search for in response text')
    return parent


def schedule_many(scheduler: Scheduler, input_queue: asyncio.Queue, config_path: str):
    with open(config_path) as fp:
        conf = yaml.safe_load(fp)
    for site in conf['sites']:
        task = {
            'url': site['url'],
            'pattern': site.get('pattern'),
            'request_kwargs': site.get('request_kwargs', {})
        }
        interval = site.get('interval', {'seconds': 60})
        scheduler.schedule(input_queue.put, interval, task)


async def main(args: argparse.Namespace, settings=EnvSettings()):
    assert args.url or args.targets_file, '--url or --targets-file argument required'

    producer = create_producer(settings, value_serializer=Serde(settings.message_encoding).serialize)

    async with KafkaPublisher(producer, settings.kafka_topic_success, settings.kafka_topic_failure) as kafka_publisher:
        await producer.start()

        input_queue = asyncio.Queue()
        scheduler = SimpleScheduler()
        task_provider = QueueTaskProvider(input_queue)
        poller = AsyncSitePoller()

        _ = Composer().run(task_provider, processors=[poller], output_handlers=[kafka_publisher])
        if args.targets_file:
            if not os.path.exists(args.targets_file):
                logger.error('configuration file not found: {}', args.targets_file)
                exit(1)
            schedule_many(scheduler, input_queue, args.targets_file)
        else:
            task = {'url': args.url, 'pattern': args.pattern}
            interval = {'seconds': args.seconds}
            scheduler.schedule(input_queue.put, interval, task)

        await asyncio.Queue().get()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(
        main(configure_parser().parse_args())
    )
