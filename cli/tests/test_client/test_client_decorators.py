import asyncio

import aiohttp
import pytest

from mock import patch

from urllib3.exceptions import HTTPError

from polyaxon._client.decorators import async_client_handler, client_handler
from polyaxon._utils.test_utils import patch_settings
from polyaxon.exceptions import ApiException


class DummyClient:
    def __init__(
        self,
        no_op=None,
        is_offline=None,
        manual_exceptions_handling=False,
    ):
        self._client = None
        self._no_op = no_op
        self._is_offline = is_offline
        self._manual_exceptions_handling = manual_exceptions_handling
        self.called = False


def setup_test_settings():
    patch_settings()


@pytest.mark.client_mark
def test_client_handler_no_op_returns_early():
    setup_test_settings()
    dummy = DummyClient(no_op=True)

    @client_handler(check_no_op=True)
    def call(self):
        self.called = True
        return "done"

    assert call(dummy) is None
    assert dummy.called is False


@pytest.mark.client_mark
def test_client_handler_offline_returns_early():
    setup_test_settings()
    dummy = DummyClient(is_offline=True)

    @client_handler(check_no_op=False, check_offline=True)
    def call(self):
        self.called = True
        return "done"

    assert call(dummy) is None
    assert dummy.called is False


@pytest.mark.client_mark
def test_client_handler_success_returns_wrapped_value():
    setup_test_settings()
    dummy = DummyClient()

    @client_handler(check_no_op=False)
    def call(self):
        self.called = True
        return "done"

    assert call(dummy) == "done"
    assert dummy.called is True


@pytest.mark.client_mark
@pytest.mark.parametrize(
    "error",
    [
        ApiException(status=500, reason="failure"),
        HTTPError("http failed"),
    ],
)
def test_client_handler_exceptions_call_error_handler(error):
    setup_test_settings()
    dummy = DummyClient()

    @client_handler(check_no_op=False)
    def call(self):
        raise error

    with patch(
        "polyaxon._client.decorators.client_call_handler.handle_client_error"
    ) as handle:
        with pytest.raises(error.__class__):
            call(dummy)

    assert handle.call_count == 1
    assert handle.call_args.kwargs["e"] is error
    assert "API Client failed at the function `call`" in handle.call_args.kwargs[
        "message"
    ]


@pytest.mark.client_mark
def test_client_handler_manual_exception_handling_passes_none():
    setup_test_settings()
    dummy = DummyClient(manual_exceptions_handling=True)
    error = ApiException(status=500, reason="failure")

    @client_handler(check_no_op=False)
    def call(self):
        raise error

    with patch(
        "polyaxon._client.decorators.client_call_handler.handle_client_error"
    ) as handle:
        with pytest.raises(ApiException):
            call(dummy)

    assert handle.call_count == 1
    assert handle.call_args.kwargs["e"] is None


@pytest.mark.client_mark
def test_client_handler_can_log_events_warning():
    setup_test_settings()
    dummy = DummyClient()

    @client_handler(check_no_op=False, can_log_events=True)
    def call(self):
        return "done"

    with patch("polyaxon._client.decorators.client_call_handler.logger.warning") as log:
        assert call(dummy) == "done"

    assert log.call_count == 1
    assert "event logger" in log.call_args.args[0]


@pytest.mark.client_mark
def test_client_handler_can_log_outputs_warning():
    setup_test_settings()
    dummy = DummyClient()

    @client_handler(check_no_op=False, can_log_outputs=True)
    def call(self):
        return "done"

    with patch("polyaxon._client.decorators.client_call_handler.logger.warning") as log:
        assert call(dummy) == "done"

    assert log.call_count == 1
    assert "outputs path" in log.call_args.args[0]


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_client_handler_no_op_returns_early():
    setup_test_settings()
    dummy = DummyClient(no_op=True)

    @async_client_handler(check_no_op=True)
    async def call(self):
        self.called = True
        return "done"

    assert await call(dummy) is None
    assert dummy.called is False


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_client_handler_offline_returns_early():
    setup_test_settings()
    dummy = DummyClient(is_offline=True)

    @async_client_handler(check_no_op=False, check_offline=True)
    async def call(self):
        self.called = True
        return "done"

    assert await call(dummy) is None
    assert dummy.called is False


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_client_handler_success_awaits_wrapped_function():
    setup_test_settings()
    dummy = DummyClient()

    @async_client_handler(check_no_op=False)
    async def call(self):
        self.called = True
        return "done"

    assert await call(dummy) == "done"
    assert dummy.called is True


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_client_handler_api_exception_calls_error_handler():
    setup_test_settings()
    dummy = DummyClient()
    error = ApiException(status=500, reason="failure")

    @async_client_handler(check_no_op=False)
    async def call(self):
        raise error

    with patch(
        "polyaxon._client.decorators.client_call_handler.handle_client_error"
    ) as handle:
        with pytest.raises(ApiException):
            await call(dummy)

    assert handle.call_count == 1
    assert handle.call_args.kwargs["e"] is error
    assert "API Client failed at the function `call`" in handle.call_args.kwargs[
        "message"
    ]


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_client_handler_manual_exception_handling_passes_none():
    setup_test_settings()
    dummy = DummyClient(manual_exceptions_handling=True)
    error = ApiException(status=500, reason="failure")

    @async_client_handler(check_no_op=False)
    async def call(self):
        raise error

    with patch(
        "polyaxon._client.decorators.client_call_handler.handle_client_error"
    ) as handle:
        with pytest.raises(ApiException):
            await call(dummy)

    assert handle.call_count == 1
    assert handle.call_args.kwargs["e"] is None


@pytest.mark.client_mark
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        aiohttp.ClientError("client failed"),
        asyncio.TimeoutError("timed out"),
    ],
)
async def test_async_client_handler_transport_errors_call_error_handler(error):
    setup_test_settings()
    dummy = DummyClient()

    @async_client_handler(check_no_op=False)
    async def call(self):
        raise error

    with patch(
        "polyaxon._client.decorators.client_call_handler.handle_client_error"
    ) as handle:
        with pytest.raises(error.__class__):
            await call(dummy)

    assert handle.call_count == 1
    assert handle.call_args.kwargs["e"] is error


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_client_handler_can_log_events_warning():
    setup_test_settings()
    dummy = DummyClient()

    @async_client_handler(check_no_op=False, can_log_events=True)
    async def call(self):
        return "done"

    with patch("polyaxon._client.decorators.client_call_handler.logger.warning") as log:
        assert await call(dummy) == "done"

    assert log.call_count == 1
    assert "event logger" in log.call_args.args[0]


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_client_handler_can_log_outputs_warning():
    setup_test_settings()
    dummy = DummyClient()

    @async_client_handler(check_no_op=False, can_log_outputs=True)
    async def call(self):
        return "done"

    with patch("polyaxon._client.decorators.client_call_handler.logger.warning") as log:
        assert await call(dummy) == "done"

    assert log.call_count == 1
    assert "outputs path" in log.call_args.args[0]
