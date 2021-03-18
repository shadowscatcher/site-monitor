import re
from datetime import datetime, timezone
from typing import Any, Callable

import loguru
from aiohttp import ClientSession, ClientError
from aiokafka import AIOKafkaProducer, ConsumerRecord

from abstractions import Worker
from db import Repository

__all__ = ['KafkaPublisher', 'AsyncSitePoller', 'DbWriter']


class KafkaPublisher(Worker):
    def __init__(self, producer: AIOKafkaProducer, topic_success: str, topic_failure: str, logger=loguru.logger):
        """
        Publishes json messages to one of given topics

        :param producer:
        :param topic_success: Topic name for messages about successful requests
        :param topic_failure: Topic name for messages about failed requests
        :param logger:
        """
        self.producer = producer
        self.topic_success = topic_success
        self.topic_failure = topic_failure
        self.logger = logger

    @loguru.logger.catch
    async def process(self, task: dict) -> Any:
        """
        Publishes response information to one of Kafka topics depending on 'success' field value

        :param task: Response information from AsyncSitePoller
        :return: None
        """
        topic = self.topic_success if task['success'] else self.topic_failure
        pub_result = await self.producer.send_and_wait(topic, task)
        self.logger.debug('published: {}', pub_result)
        self.logger.info('message sent: {}', task)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.producer.stop()


class AsyncSitePoller(Worker):
    def __init__(self, session_kwargs: dict = None, session_factory: Callable[[dict], ClientSession] = None, 
        logger=loguru.logger):
        """
        Can poll urls with big variety of options

        :param session_kwargs: Args for session constructor, like headers, timeouts, auth and more
        :param session_factory: Use it if you want to control session creation
        :param logger:
        """
        self.session_kwargs = session_kwargs or {}
        self.session_factory = session_factory if session_factory else lambda kw: ClientSession(**kw)
        self.logger = logger

    @loguru.logger.catch
    async def process(self, task: dict) -> Any:
        """
        Issues HTTP requests and returns data about operation result

        :param task: must have 'url' key, can have 'pattern'
        :return: Info about response time or error description
        """
        assert 'url' in task, 'Site poller requires url to fetch data from'
        url = task['url']
        method = task.get('method', 'GET')
        pattern = task.get('pattern')
        request_kwargs = task.get('request_kwargs', {})

        data = await self.request(method, url, **request_kwargs)
        data['url'] = url
        if pattern and data['success']:
            try:
                data['match'] = bool(re.search(pattern, data['text']))
                data['pattern'] = pattern
            except re.error as e:
                self.logger.error('error matching text with pattern {}: {}', pattern, e)
        if 'text' in data:
            del data['text']
        return data

    async def request(self, method: str, url: str, **kwargs) -> dict:
        """
        Issues HTTP requests to target URL. Only handles aiohttp errors

        :param method: HTTP verb
        :param url:
        :param kwargs: any request kwargs, like proxy, headers or timeouts
        :return:
        """
        started = datetime.now(timezone.utc).astimezone()

        async with self.session_factory(self.session_kwargs) as session:
            try:
                async with session.request(method, url, **kwargs) as response:
                    ended = datetime.now(timezone.utc).astimezone()
                    text = await response.text()
                    status = response.status

                    return {
                        'started': started.isoformat(),
                        'ended': ended.isoformat(),
                        'response_time_s': (ended - started).total_seconds(),
                        'text': text,
                        'status': status,
                        'success': True
                    }
            except ClientError as e:
                self.logger.exception('error requesting url {}', url)
                return {
                    'started': started.isoformat(),
                    'success': False,
                    'error_type': str(type(e)),
                    'message': str(e)
                }


class DbWriter(Worker):
    def __init__(self, repo: Repository, topic_success: str, topic_failure: str, logger=loguru.logger,
                 success_callback: Callable[[ConsumerRecord], None] = None):
        """
        Stores messages in database

        :param repo: Db methods provider
        :param topic_success: name of topic with successful tasks
        :param topic_failure: name of topic with errors
        :param logger:
        :param success_callback: if provided, will be called with received ConsumerRecord after save
        """
        self.repo = repo
        self.topic_success = topic_success
        self.topic_failure = topic_failure
        self.logger = logger
        self.success_callback = success_callback

    @loguru.logger.catch
    async def process(self, task: ConsumerRecord) -> Any:
        self.logger.debug('received record: {}', task)
        if task.topic == self.topic_success:
            await self.repo.save_successful_check(task.value)
            self.logger.info('saved state for url: {}', task.value.get('url'))
        elif task.topic == self.topic_failure:
            await self.repo.save_failed_check(task.value)
            self.logger.info('saved error info for url: {}', task.value.get('url'))
        else:
            self.logger.info('unknown topic: {}. No action will be taken', task.topic)

        if self.success_callback:
            self.success_callback(task)
