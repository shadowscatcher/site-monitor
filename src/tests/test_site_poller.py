import asyncio

import aiohttp
import pytest
from aioresponses import aioresponses

from impl import AsyncSitePoller


@pytest.mark.integration
def test_site_poller():
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(AsyncSitePoller().process({'url':'https://httpbin.org'}))
    assert response['status'] == 200


@pytest.mark.parametrize('url,pattern,text,expected_match', [
    ('http://test_1', 'test', '<html>contains test</htmk>', True),
    ('http://test_2', 'test', '<html>no matches</htmk>', False),
])
def test_poller_regexp(url, pattern, text, expected_match):
    task = {
        'url': url,
        'pattern': pattern
    }

    loop = asyncio.get_event_loop()
    with aioresponses() as mock:
        mock.get(url, status=200, body=text)

        result = loop.run_until_complete(AsyncSitePoller().process(task))
        assert result['match'] == expected_match


def test_poller_negative():
    task = {
        'url': 'test_url'
    }

    loop = asyncio.get_event_loop()
    with aioresponses() as mock:
        mock.get('test_url', status=200, exception=aiohttp.ClientPayloadError('test_msg'))

        result = loop.run_until_complete(AsyncSitePoller().process(task))
        assert not result['success'], 'success must be False'
        assert 'ClientPayloadError' in result['error_type']
        assert result['message'] == 'test_msg'
