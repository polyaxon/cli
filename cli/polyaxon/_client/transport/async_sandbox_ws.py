import asyncio

import aiohttp

from clipped.utils.encoding import BytesLike, as_bytes
from clipped.utils.json import orjson_dumps
from polyaxon._sandbox.client_utils import parse_ws_event
from polyaxon.exceptions import PolyaxonClientException


async def connect(url: str, headers=None, timeout=None):
    session = aiohttp.ClientSession(timeout=timeout, trust_env=True)
    try:
        ws = await session.ws_connect(url, headers=headers)
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        await session.close()
        raise PolyaxonClientException("pty.attach failed: {}".format(e)) from e
    return session, ws


async def recv_message(ws):
    while True:
        try:
            message = await ws.receive()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise PolyaxonClientException(
                "pty websocket recv failed: {}".format(e)
            ) from e

        if message.type == aiohttp.WSMsgType.BINARY:
            return message.data
        if message.type == aiohttp.WSMsgType.TEXT:
            return parse_ws_event(message.data)
        if message.type in (
            aiohttp.WSMsgType.CLOSE,
            aiohttp.WSMsgType.CLOSED,
            aiohttp.WSMsgType.CLOSING,
        ):
            raise PolyaxonClientException("PTY websocket closed.")
        if message.type == aiohttp.WSMsgType.ERROR:
            error = ws.exception()
            raise PolyaxonClientException(
                "PTY websocket error{}.".format(": {}".format(error) if error else "")
            )
        if message.type in (aiohttp.WSMsgType.PING, aiohttp.WSMsgType.PONG):
            continue
        raise PolyaxonClientException("Unsupported PTY websocket frame.")


class AsyncSandboxPtyWSClient:
    def __init__(self, session, ws, attached_event):
        self._session = session
        self._ws = ws
        self._attached_event = attached_event

    @property
    def attached_event(self):
        return self._attached_event

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()

    async def send_stdin(self, data: BytesLike):
        try:
            await self._ws.send_bytes(as_bytes(data))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise PolyaxonClientException(
                "pty websocket send failed: {}".format(e)
            ) from e

    async def send_control(self, event):
        try:
            await self._ws.send_str(orjson_dumps(event))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise PolyaxonClientException(
                "pty websocket send failed: {}".format(e)
            ) from e

    async def recv(self):
        return await recv_message(self._ws)

    async def close(self):
        try:
            await self._ws.close()
            await self._session.close()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise PolyaxonClientException(
                "pty websocket close failed: {}".format(e)
            ) from e
