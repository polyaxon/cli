import pytest

from mock import patch

from polyaxon import settings
from polyaxon._client.mixin import ClientMixin
from polyaxon._utils.test_utils import patch_settings
from polyaxon.exceptions import PolyaxonClientException


class SDKClientMock:
    def __init__(self, is_async=False, name=None, events=None):
        self.is_async = is_async
        self.name = name
        self.events = events
        self.close_calls = 0
        self.aclose_calls = 0

    def close(self):
        self.close_calls += 1
        if self.events is not None:
            self.events.append("{}:close".format(self.name))

    async def aclose(self):
        self.aclose_calls += 1
        if self.events is not None:
            self.events.append("{}:aclose".format(self.name))


class DummyClient(ClientMixin):
    pass


class AsyncDummyClient(ClientMixin):
    _IS_ASYNC = True


class AsyncFlushClient(AsyncDummyClient):
    def __init__(self, events):
        self.events = events

    async def _flush_on_exit(self) -> None:
        self.events.append("flush")


def setup_test_settings():
    patch_settings()


@pytest.mark.client_mark
class TestClientMixin:
    def test_lazy_client_creation_marks_as_owned(self):
        setup_test_settings()
        client = SDKClientMock()
        mixin = DummyClient()
        with patch("polyaxon._client.mixin.PolyaxonClient", return_value=client) as cls:
            assert mixin.client is client

        cls.assert_called_once_with(is_async=False)
        assert mixin._client is client
        assert mixin._owns_client is True

    def test_injected_client_marks_as_not_owned(self):
        client = SDKClientMock()
        mixin = DummyClient()

        mixin._set_client(client)

        assert mixin._client is client
        assert mixin._owns_client is False

    def test_injected_sync_client_into_async_mixin_raises(self):
        client = SDKClientMock(is_async=False)
        mixin = AsyncDummyClient()

        with pytest.raises(PolyaxonClientException):
            mixin._set_client(client)

    def test_injected_async_client_into_sync_mixin_raises(self):
        client = SDKClientMock(is_async=True)
        mixin = DummyClient()

        with pytest.raises(PolyaxonClientException):
            mixin._set_client(client)

    def test_lazy_client_uses_async_when_class_is_async(self):
        setup_test_settings()
        client = SDKClientMock(is_async=True)
        mixin = AsyncDummyClient()
        with patch("polyaxon._client.mixin.PolyaxonClient", return_value=client) as cls:
            assert mixin.client is client

        cls.assert_called_once_with(is_async=True)
        assert mixin._owns_client is True

    def test_reset_client_raises_on_async_mixin(self):
        mixin = AsyncDummyClient()

        with pytest.raises(PolyaxonClientException):
            mixin.reset_client()

    def test_reset_client_closes_previous_after_replacement(self):
        setup_test_settings()
        events = []
        previous = SDKClientMock(name="previous", events=events)
        replacement = SDKClientMock(name="replacement", events=events)
        mixin = DummyClient()
        mixin._client = previous
        mixin._owns_client = True

        def build_client(*args, **kwargs):
            events.append("replacement:make")
            return replacement

        with patch("polyaxon._client.mixin.PolyaxonClient") as cls:
            cls.side_effect = build_client
            mixin.reset_client(host="localhost")

        assert mixin._client is replacement
        assert mixin._owns_client is True
        assert events == ["replacement:make", "previous:close"]
        assert cls.call_args.kwargs == {"is_async": False}

    def test_reset_client_in_cluster_is_noop(self):
        setup_test_settings()
        settings.CLIENT_CONFIG.in_cluster = True
        try:
            previous = SDKClientMock()
            mixin = DummyClient()
            mixin._client = previous
            mixin._owns_client = True

            with patch("polyaxon._client.mixin.PolyaxonClient") as cls:
                mixin.reset_client(host="localhost")

            assert cls.call_count == 0
            assert mixin._client is previous
            assert previous.close_calls == 0
        finally:
            settings.CLIENT_CONFIG.in_cluster = False

    def test_owned_sync_client_closes_on_context_exit(self):
        client = SDKClientMock()
        mixin = DummyClient()
        mixin._client = client
        mixin._owns_client = True

        with mixin:
            pass

        assert client.close_calls == 1

    def test_injected_sync_client_does_not_close_on_context_exit(self):
        client = SDKClientMock()
        mixin = DummyClient()
        mixin._set_client(client)

        with mixin:
            pass

        assert client.close_calls == 0

    def test_sync_context_manager_raises_on_async_mixin(self):
        mixin = AsyncDummyClient()

        with pytest.raises(PolyaxonClientException):
            with mixin:
                pass


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_areset_client_raises_on_sync_mixin():
    mixin = DummyClient()

    with pytest.raises(PolyaxonClientException):
        await mixin.areset_client()


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_areset_client_closes_previous_after_replacement():
    setup_test_settings()
    events = []
    previous = SDKClientMock(is_async=True, name="previous", events=events)
    replacement = SDKClientMock(is_async=True, name="replacement", events=events)
    mixin = AsyncDummyClient()
    mixin._client = previous
    mixin._owns_client = True

    def build_client(*args, **kwargs):
        events.append("replacement:make")
        return replacement

    with patch("polyaxon._client.mixin.PolyaxonClient") as cls:
        cls.side_effect = build_client
        await mixin.areset_client(host="localhost")

    assert mixin._client is replacement
    assert mixin._owns_client is True
    assert events == ["replacement:make", "previous:aclose"]
    assert cls.call_args.kwargs == {"is_async": True}


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_areset_client_in_cluster_is_noop():
    setup_test_settings()
    settings.CLIENT_CONFIG.in_cluster = True
    try:
        previous = SDKClientMock(is_async=True)
        mixin = AsyncDummyClient()
        mixin._client = previous
        mixin._owns_client = True

        with patch("polyaxon._client.mixin.PolyaxonClient") as cls:
            await mixin.areset_client(host="localhost")

        assert cls.call_count == 0
        assert mixin._client is previous
        assert previous.aclose_calls == 0
    finally:
        settings.CLIENT_CONFIG.in_cluster = False


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_flush_on_exit_default_is_noop():
    mixin = AsyncDummyClient()

    assert await mixin._flush_on_exit() is None


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_owned_async_client_closes_on_context_exit():
    client = SDKClientMock(is_async=True)
    mixin = AsyncDummyClient()
    mixin._client = client
    mixin._owns_client = True

    async with mixin:
        pass

    assert client.aclose_calls == 1


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_injected_async_client_does_not_close_on_context_exit():
    client = SDKClientMock(is_async=True)
    mixin = AsyncDummyClient()
    mixin._set_client(client)

    async with mixin:
        pass

    assert client.aclose_calls == 0


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_context_manager_raises_on_sync_mixin():
    mixin = DummyClient()

    with pytest.raises(PolyaxonClientException):
        async with mixin:
            pass


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_context_manager_flushes_before_close():
    events = []
    client = SDKClientMock(is_async=True, name="client", events=events)
    mixin = AsyncFlushClient(events=events)
    mixin._client = client
    mixin._owns_client = True

    async with mixin:
        pass

    assert events == ["flush", "client:aclose"]


@pytest.mark.client_mark
@pytest.mark.asyncio
async def test_async_context_manager_closes_when_flush_raises():
    class FailingFlushClient(AsyncDummyClient):
        async def _flush_on_exit(self) -> None:
            raise RuntimeError("flush failed")

    client = SDKClientMock(is_async=True)
    mixin = FailingFlushClient()
    mixin._client = client
    mixin._owns_client = True

    with pytest.raises(RuntimeError):
        async with mixin:
            pass

    assert client.aclose_calls == 1
