import pytest

from kubernetes import client

from polyaxon._k8s.manager.manager import K8sManager
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
class TestK8sManager(BaseTestCase):
    def test_init_with_configuration(self):
        configuration = client.Configuration(host="https://k8s.local")
        manager = K8sManager(namespace="polyaxon", k8s_config=configuration)

        assert isinstance(manager.api_client, client.ApiClient)
        assert manager.api_client.configuration is configuration
