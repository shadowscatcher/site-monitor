import asyncio

from common.composer import Composer
from tests.mock import MockSitePoller, MockProvider, MockPublisher


def test_composer():
    """
    Tests whole pipeline execution
    """
    final = asyncio.Queue()
    provider = MockProvider({'url': 'https://example.com'})
    processor = MockSitePoller()
    publisher = MockPublisher(final)

    async def schedule_all():
        tasks = Composer().run(provider, [processor], [publisher])
        results = await final.get()
        for t in tasks:
            t.cancel()
        return results

    result = asyncio.get_event_loop().run_until_complete(schedule_all())

    assert list(result) == ['url', 'status', 'text', 'pattern', 'match', 'started', 'ended', 'elapsed']
    assert result['url'] == 'https://example.com'
