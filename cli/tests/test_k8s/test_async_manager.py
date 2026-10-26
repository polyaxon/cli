import mock
import pytest
from unittest import IsolatedAsyncioTestCase

from kubernetes.aio import client

from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
@mock.patch("polyaxon._k8s.manager.async_manager.config.load_incluster_config")
@mock.patch(
    "polyaxon._k8s.manager.async_manager.config.load_kube_config",
    new_callable=mock.AsyncMock,
)
class TestAsyncK8sManager(BaseTestCase, IsolatedAsyncioTestCase):
    async def test_load_config(self, load_kube_config, load_incluster_config):
        configuration = await AsyncK8sManager.load_config(in_cluster=True)
        assert isinstance(configuration, client.Configuration)
        load_incluster_config.assert_called_once_with()
        load_kube_config.assert_not_awaited()

        configuration = await AsyncK8sManager.load_config()
        assert isinstance(configuration, client.Configuration)
        load_kube_config.assert_awaited_once_with()

    async def test_setup_with_kube_config(
        self, load_kube_config, load_incluster_config
    ):
        manager = AsyncK8sManager(namespace="polyaxon")
        await manager.setup()

        load_kube_config.assert_awaited_once_with()
        load_incluster_config.assert_not_called()
        assert isinstance(manager.api_client, client.ApiClient)
        await manager.close()

    async def test_setup_in_cluster(self, load_kube_config, load_incluster_config):
        manager = AsyncK8sManager(namespace="polyaxon", in_cluster=True)
        await manager.setup()

        load_incluster_config.assert_called_once_with()
        load_kube_config.assert_not_awaited()
        assert isinstance(manager.api_client, client.ApiClient)
        await manager.close()

    async def test_setup_with_configuration(
        self, load_kube_config, load_incluster_config
    ):
        configuration = client.Configuration(host="https://k8s.local")
        manager = AsyncK8sManager(namespace="polyaxon")
        await manager.setup(k8s_config=configuration)

        load_kube_config.assert_not_awaited()
        load_incluster_config.assert_not_called()
        assert manager.api_client.configuration is configuration

        close = mock.AsyncMock(wraps=manager.api_client.close)
        with mock.patch.object(manager.api_client, "close", close):
            await manager.close()
        close.assert_awaited_once_with()
