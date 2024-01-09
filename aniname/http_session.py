"""
Contains the aiohttp session used for fetching data.
"""

import aiohttp

_client_session = None


async def get_client_session():
    global _client_session

    if _client_session is None:
        _client_session = aiohttp.ClientSession()

    return _client_session


async def close_client_session():
    global _client_session

    if _client_session is not None:
        await _client_session.close()
        _client_session = None
