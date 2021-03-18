import asyncio
from typing import NamedTuple

from impl import DbWriter
from tests.mock.repository import MockRepository


class MockRecord(NamedTuple):
    value: dict
    topic: str


def test_message_saver():
    topic_success, topic_failure = 'ts',  'tf'
    success_record, failure_record = MockRecord({'success': True}, topic_success), MockRecord({'success': False}, topic_failure)
    repo = MockRepository()
    writer = DbWriter(repo, topic_success, topic_failure)
    loop = asyncio.get_event_loop()

    loop.run_until_complete(asyncio.gather(
        writer.process(success_record),
        writer.process(failure_record)
    ))

    assert repo.success == [success_record.value], 'successful message was incorrectly saved'
    assert repo.fail == [failure_record.value], 'failure report was incorrectly saved'
