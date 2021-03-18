"""
Convenient factories for kafka clients - for test environment and prod environment with SSL authentication
"""

from ssl import SSLContext

import loguru
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.helpers import create_ssl_context

from common.settings import EnvSettings


def ssl_context(settings: EnvSettings) -> SSLContext:
    return create_ssl_context(
        cafile=settings.kafka_cafile,
        certfile=settings.kafka_certfile,
        keyfile=settings.kafka_keyile
    )


@loguru.logger.catch(reraise=True)
def create_producer(settings: EnvSettings, **kwargs) -> AIOKafkaProducer:
    if all((settings.kafka_keyile, settings.kafka_cafile, settings.kafka_certfile)):
        return AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            security_protocol='SSL',
            ssl_context=ssl_context(settings),
            **kwargs
        )

    return AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers, **kwargs)


@loguru.logger.catch(reraise=True)
def create_consumer(settings: EnvSettings, **kwargs) -> AIOKafkaConsumer:
    if all((settings.kafka_keyile, settings.kafka_cafile, settings.kafka_certfile)):
        return AIOKafkaConsumer(
            settings.kafka_topic_success, settings.kafka_topic_failure,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            security_protocol='SSL',
            ssl_context=ssl_context(settings),
            group_id=settings.kafka_consumer_group,
            **kwargs
        )

    return AIOKafkaConsumer(settings.kafka_topic_success, settings.kafka_topic_failure,
                            bootstrap_servers=settings.kafka_bootstrap_servers, group_id=settings.kafka_consumer_group,
                            **kwargs)
