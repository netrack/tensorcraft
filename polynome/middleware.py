import aiohttp.web
import semver

from aiohttp import web
from aiojobs.aiohttp import atomic
from typing import Awaitable


def handle_accept_version(req: aiohttp.web.Request, api_version: str):
    default_version = "=={0}".format(api_version)
    req_version = req.headers.get("Accept-Version", default_version)

    try:
        match = semver.match(api_version, req_version)
    except ValueError as e:
        raise aiohttp.web.HTTPNotAcceptable(text=str(e))
    else:
        if not match:
            text = ("accept version {0} does not match API version {1}"
                    ).format(req_version, api_version)
            raise aiohttp.web.HTTPNotAcceptable(text=text)


def accept_version(handler: Awaitable, api_version: str) -> Awaitable:
    async def _f(req: aiohttp.web.Request) -> aiohttp.web.Response:
        handle_accept_version(req, api_version)
        return await handler(req)
    return _f


def route_to(handler: Awaitable, api_version: str) -> Awaitable:
    """Create a route with the API version validation.

    Returns handler decorated with API version check.
    """
    return atomic(accept_version(handler, api_version))
