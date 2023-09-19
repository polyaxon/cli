import pytest

from polyaxon.connections import V1ConnectionResource
from polyaxon.docker import docker_types
from polyaxon.docker.converter.base.env_vars import EnvMixin
from polyaxon.env_vars.keys import (
    ENV_KEYS_API_VERSION,
    ENV_KEYS_AUTH_TOKEN,
    ENV_KEYS_AUTHENTICATION_TYPE,
    ENV_KEYS_HEADER,
    ENV_KEYS_HEADER_SERVICE,
    ENV_KEYS_HOST,
    ENV_KEYS_IS_MANAGED,
    ENV_KEYS_K8S_NAMESPACE,
    ENV_KEYS_K8S_POD_ID,
    ENV_KEYS_RUN_INSTANCE,
    ENV_KEYS_SECRET_INTERNAL_TOKEN,
    ENV_KEYS_SECRET_KEY,
)
from polyaxon.exceptions import PolyaxonConverterError
from tests.test_docker.test_converters.base import BaseConverterTest


@pytest.mark.docker_mark
class TestEnvVars(BaseConverterTest):
    def test_get_env_vars(self):
        # String value
        env_var = EnvMixin._get_env_var(name="foo", value="bar")
        assert env_var == docker_types.V1EnvVar(__root__=("foo", "bar"))
        # Int value
        env_var = EnvMixin._get_env_var(name="foo", value=1)
        assert env_var == docker_types.V1EnvVar(__root__=("foo", "1"))
        # Dict value
        env_var = EnvMixin._get_env_var(name="foo", value={"moo": "bar"})
        assert env_var == docker_types.V1EnvVar(__root__=("foo", '{"moo":"bar"}'))

    def test_get_kv_env_var(self):
        # Empty value
        assert EnvMixin._get_kv_env_vars([]) == []
        # Non valid value
        with self.assertRaises(PolyaxonConverterError):
            EnvMixin._get_kv_env_vars([[123, "foo", "bar"]])
        with self.assertRaises(PolyaxonConverterError):
            EnvMixin._get_kv_env_vars([[123]])
        # Valid value
        env_vars = EnvMixin._get_kv_env_vars(
            [["foo", {"moo": "bar"}], ("foo", "bar"), ["foo", 1]]
        )
        assert env_vars[0].__root__[0] == "foo"
        assert env_vars[0].__root__[1] == '{"moo":"bar"}'
        assert env_vars[1].__root__[0] == "foo"
        assert env_vars[1].__root__[1] == "bar"
        assert env_vars[2].__root__[0] == "foo"
        assert env_vars[2].__root__[1] == "1"

    def test_get_from_resource(self):
        assert (
            EnvMixin._get_item_from_json_resource(key="foo", resource_ref_name="cm_ref")
            is None
        )

    def test_get_items_from_resource(self):
        # None
        assert EnvMixin._get_items_from_json_resource(None) == []
        # Secret without items
        secret = V1ConnectionResource(name="test", is_requested=True)
        assert EnvMixin._get_items_from_json_resource(secret) == []
        secret = V1ConnectionResource(
            name="test",
            items=[],
            is_requested=True,
        )
        assert EnvMixin._get_items_from_json_resource(secret) == []
        # Secret with items
        secret = V1ConnectionResource(
            name="test",
            items=["item1", "item2"],
            is_requested=True,
        )
        assert EnvMixin._get_items_from_json_resource(secret) == []

    def get_items_from_config_map(self):
        # None
        assert EnvMixin._get_items_from_secret(None) == []
        # Secret without items
        secret = V1ConnectionResource(name="test", is_requested=True)
        assert EnvMixin._get_items_from_secret(secret) == []
        secret = V1ConnectionResource(
            name="test",
            items=[],
            is_requested=True,
        )
        assert EnvMixin._get_items_from_secret(secret) == []
        # Secret with items
        secret = V1ConnectionResource(
            name="test",
            items=["item1", "item2"],
            is_requested=True,
        )
        assert EnvMixin._get_items_from_secret(secret) == [
            EnvMixin._get_from_config_map("item1", "item1", secret.name),
            EnvMixin._get_from_config_map("item2", "item2", secret.name),
        ]

    def test_get_env_vars_from_k8s_resources(self):
        assert (
            EnvMixin._get_env_vars_from_k8s_resources(secrets=[], config_maps=[]) == []
        )
        res1 = V1ConnectionResource(name="test", is_requested=True)
        res2 = V1ConnectionResource(name="test2", is_requested=True)
        assert (
            EnvMixin._get_env_vars_from_k8s_resources(
                secrets=[res1, res2], config_maps=[]
            )
            == []
        )
        assert (
            EnvMixin._get_env_vars_from_k8s_resources(
                secrets=[res1], config_maps=[res2]
            )
            == []
        )
        assert (
            EnvMixin._get_env_vars_from_k8s_resources(
                secrets=[], config_maps=[res1, res2]
            )
            == []
        )

        res1 = V1ConnectionResource(
            name="test",
            items=["item1", "item2"],
            is_requested=True,
        )
        res2 = V1ConnectionResource(
            name="test2",
            items=["item1", "item2"],
            is_requested=True,
        )
        assert (
            EnvMixin._get_env_vars_from_k8s_resources(
                secrets=[res1, res2], config_maps=[]
            )
            == []
        )
        assert (
            EnvMixin._get_env_vars_from_k8s_resources(
                secrets=[res1], config_maps=[res2]
            )
            == []
        )
        assert (
            EnvMixin._get_env_vars_from_k8s_resources(
                secrets=[], config_maps=[res1, res2]
            )
            == []
        )

    def test_get_env_from_resource(self):
        # None
        assert EnvMixin._get_from_json_resource(resource=None) == []
        # ConfigMap with items
        config_map = V1ConnectionResource(
            name="test",
            items=["item1", "item2"],
            is_requested=True,
        )
        assert EnvMixin._get_from_json_resource(resource=config_map) == []

        # ConfigMap
        config_map = V1ConnectionResource(name="test_ref", is_requested=True)

        assert EnvMixin._get_from_json_resource(resource=config_map) == []

    def test_get_env_from_resources(self):
        # None
        assert EnvMixin._get_env_from_json_resources(resources=None) == []
        # Secret with items
        secret1 = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            is_requested=True,
        )
        # Secret
        secret2 = V1ConnectionResource(
            name="test_ref",
            is_requested=True,
        )

        assert EnvMixin._get_env_from_json_resources(resources=[secret1, secret2]) == []

    def test_get_run_instance_env_var(self):
        assert EnvMixin._get_run_instance_env_var(
            "run_instance"
        ) == EnvMixin._get_env_var(name=ENV_KEYS_RUN_INSTANCE, value="run_instance")

    def test_get_service_env_vars_raises_for_internal_and_agent_token(self):
        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_service_env_vars(
                header=None,
                service_header=None,
                include_secret_key=False,
                include_internal_token=True,
                include_agent_token=True,
                authentication_type=None,
                log_level=None,
                polyaxon_default_secret_ref="polyaxon-secret",
                polyaxon_agent_secret_ref="polyaxon-agent",
                external_host=False,
                api_version="v1",
                use_proxy_env_vars_use_in_ops=False,
            )

    def test_get_service_env_vars(self):
        env_vars = self.converter._get_service_env_vars(
            header=None,
            service_header=None,
            include_secret_key=False,
            include_internal_token=False,
            include_agent_token=False,
            authentication_type=None,
            log_level=None,
            polyaxon_default_secret_ref="polyaxon-secret",
            polyaxon_agent_secret_ref="polyaxon-agent",
            external_host=False,
            api_version="v1",
            use_proxy_env_vars_use_in_ops=False,
        )
        assert len(env_vars) == 7
        env_var_names = [env_var.__root__[0] for env_var in env_vars]
        assert ENV_KEYS_K8S_POD_ID in env_var_names
        assert ENV_KEYS_K8S_NAMESPACE in env_var_names
        assert ENV_KEYS_HOST in env_var_names
        assert ENV_KEYS_IS_MANAGED in env_var_names
        assert ENV_KEYS_API_VERSION in env_var_names
        assert ENV_KEYS_RUN_INSTANCE in env_var_names

        env_vars = self.converter._get_service_env_vars(
            header="foo",
            service_header="foo",
            include_secret_key=True,
            include_internal_token=True,
            include_agent_token=False,
            log_level=None,
            authentication_type="foo",
            polyaxon_default_secret_ref="polyaxon-secret",
            polyaxon_agent_secret_ref="polyaxon-agent",
            external_host=False,
            api_version="v1",
            use_proxy_env_vars_use_in_ops=False,
        )
        assert len(env_vars) == 10  # Normally 12
        env_var_names = [env_var.__root__[0] for env_var in env_vars]
        assert ENV_KEYS_K8S_POD_ID in env_var_names
        assert ENV_KEYS_K8S_NAMESPACE in env_var_names
        assert ENV_KEYS_HOST in env_var_names
        assert ENV_KEYS_IS_MANAGED in env_var_names
        assert ENV_KEYS_API_VERSION in env_var_names
        assert ENV_KEYS_HEADER in env_var_names
        assert ENV_KEYS_HEADER_SERVICE in env_var_names
        assert ENV_KEYS_SECRET_KEY not in env_var_names  # This should be in the agent
        assert (
            ENV_KEYS_SECRET_INTERNAL_TOKEN not in env_var_names
        )  # This should be in the agent
        assert ENV_KEYS_AUTHENTICATION_TYPE in env_var_names
        assert ENV_KEYS_RUN_INSTANCE in env_var_names

        env_vars = self.converter._get_service_env_vars(
            header="foo",
            service_header="foo",
            include_secret_key=True,
            include_internal_token=False,
            include_agent_token=True,
            log_level=None,
            authentication_type="foo",
            polyaxon_default_secret_ref="polyaxon-secret",
            polyaxon_agent_secret_ref="polyaxon-agent",
            external_host=False,
            api_version="v1",
            use_proxy_env_vars_use_in_ops=False,
        )
        assert len(env_vars) == 10  # Normally 12
        env_var_names = [env_var.__root__[0] for env_var in env_vars]
        assert ENV_KEYS_K8S_POD_ID in env_var_names
        assert ENV_KEYS_K8S_NAMESPACE in env_var_names
        assert ENV_KEYS_HOST in env_var_names
        assert ENV_KEYS_IS_MANAGED in env_var_names
        assert ENV_KEYS_API_VERSION in env_var_names
        assert ENV_KEYS_HEADER in env_var_names
        assert ENV_KEYS_HEADER_SERVICE in env_var_names
        assert ENV_KEYS_SECRET_KEY not in env_var_names  # This should be in the agent
        assert ENV_KEYS_AUTH_TOKEN not in env_var_names  # This should be in the agent
        assert ENV_KEYS_AUTHENTICATION_TYPE in env_var_names
        assert ENV_KEYS_RUN_INSTANCE in env_var_names
