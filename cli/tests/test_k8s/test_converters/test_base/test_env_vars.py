import pytest

from polyaxon._connections import V1ConnectionResource
from polyaxon._env_vars.keys import (
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
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.base.env_vars import EnvMixin
from polyaxon.exceptions import PolyaxonConverterError
from tests.test_k8s.test_converters.base import BaseConverterTest


@pytest.mark.k8s_mark
class TestEnvVars(BaseConverterTest):
    def test_get_env_vars(self):
        # String value
        env_var = EnvMixin._get_env_var(name="foo", value="bar")
        assert env_var.name == "foo"
        assert env_var.value == "bar"
        # Int value
        env_var = EnvMixin._get_env_var(name="foo", value=1)
        assert env_var.name == "foo"
        assert env_var.value == "1"
        # Dict value
        env_var = EnvMixin._get_env_var(name="foo", value={"moo": "bar"})
        assert env_var.name == "foo"
        assert env_var.value == '{"moo":"bar"}'

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
        assert env_vars[0].name == "foo"
        assert env_vars[0].value == '{"moo":"bar"}'
        assert env_vars[1].name == "foo"
        assert env_vars[1].value == "bar"
        assert env_vars[2].name == "foo"
        assert env_vars[2].value == "1"

    def test_get_resources_env_vars(self):
        env_vars = EnvMixin._get_resources_env_vars(None)
        assert len(env_vars) == 1
        assert env_vars[0].name == "NVIDIA_VISIBLE_DEVICES"
        assert env_vars[0].value == "none"

        resources = k8s_schemas.V1ResourceRequirements(limits={"cpu": 1})
        env_vars = EnvMixin._get_resources_env_vars(resources)
        assert len(env_vars) == 1
        assert env_vars[0].name == "NVIDIA_VISIBLE_DEVICES"
        assert env_vars[0].value == "none"

        resources = k8s_schemas.V1ResourceRequirements(limits={"memory": 1})
        env_vars = EnvMixin._get_resources_env_vars(resources)
        assert len(env_vars) == 1
        assert env_vars[0].name == "NVIDIA_VISIBLE_DEVICES"
        assert env_vars[0].value == "none"

        resources = k8s_schemas.V1ResourceRequirements(limits={"nvidia.com/gpu": 0})
        env_vars = EnvMixin._get_resources_env_vars(resources)
        assert len(env_vars) == 1
        assert env_vars[0].name == "NVIDIA_VISIBLE_DEVICES"
        assert env_vars[0].value == "none"

        resources = k8s_schemas.V1ResourceRequirements(requests={"nvidia.com/gpu": 1})
        env_vars = EnvMixin._get_resources_env_vars(resources)
        assert len(env_vars) == 0
        assert env_vars == []

    def test_get_from_config_map(self):
        env_var = EnvMixin._get_from_config_map(
            key_name="foo", config_map_key_name="cm_key", config_map_ref_name="cm_ref"
        )
        assert env_var.name == "foo"
        assert isinstance(env_var.value_from, k8s_schemas.V1EnvVarSource)
        assert env_var.value_from.config_map_key_ref.name == "cm_ref"
        assert env_var.value_from.config_map_key_ref.key == "cm_key"

    def test_get_from_secret(self):
        env_var = EnvMixin._get_from_secret(
            key_name="foo", secret_key_name="secret_key", secret_ref_name="secret_ref"
        )
        assert env_var.name == "foo"
        assert isinstance(env_var.value_from, k8s_schemas.V1EnvVarSource)
        assert env_var.value_from.secret_key_ref.name == "secret_ref"
        assert env_var.value_from.secret_key_ref.key == "secret_key"

    def test_get_items_from_secret(self):
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
            EnvMixin._get_from_secret("item1", "item1", secret.name),
            EnvMixin._get_from_secret("item2", "item2", secret.name),
        ]

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
        expected = EnvMixin._get_items_from_secret(
            res1
        ) + EnvMixin._get_items_from_secret(res2)
        assert (
            EnvMixin._get_env_vars_from_k8s_resources(
                secrets=[res1, res2], config_maps=[]
            )
            == expected
        )
        expected = EnvMixin._get_items_from_secret(
            res1
        ) + EnvMixin._get_items_from_config_map(res2)
        assert (
            EnvMixin._get_env_vars_from_k8s_resources(
                secrets=[res1], config_maps=[res2]
            )
            == expected
        )
        expected = EnvMixin._get_items_from_config_map(
            res1
        ) + EnvMixin._get_items_from_config_map(res2)
        assert (
            EnvMixin._get_env_vars_from_k8s_resources(
                secrets=[], config_maps=[res1, res2]
            )
            == expected
        )

    def test_get_from_field_ref(self):
        env_var = EnvMixin._get_from_field_ref(name="test", field_path="metadata.name")
        assert env_var.name == "test"
        assert env_var.value_from.field_ref.field_path == "metadata.name"

    def test_get_env_from_secret(self):
        # None
        assert EnvMixin._get_env_from_secret(secret=None) is None
        # Secret with items
        secret = V1ConnectionResource(
            name="test",
            items=["item1", "item2"],
            is_requested=True,
        )
        assert EnvMixin._get_env_from_secret(secret=secret) is None

        # Secret
        secret = V1ConnectionResource(name="test_ref", is_requested=True)

        assert EnvMixin._get_env_from_secret(secret=secret).secret_ref == {
            "name": "test_ref"
        }

    def test_get_env_from_config_map(self):
        # None
        assert EnvMixin._get_env_from_config_map(config_map=None) is None
        # ConfigMap with items
        config_map = V1ConnectionResource(
            name="test",
            items=["item1", "item2"],
            is_requested=True,
        )
        assert EnvMixin._get_env_from_config_map(config_map=config_map) is None

        # ConfigMap
        config_map = V1ConnectionResource(name="test_ref", is_requested=True)

        assert EnvMixin._get_env_from_config_map(
            config_map=config_map
        ).config_map_ref == {"name": "test_ref"}

    def test_get_env_from_secrets(self):
        # None
        assert EnvMixin._get_env_from_secrets(secrets=None) == []
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

        assert EnvMixin._get_env_from_secrets(secrets=[secret1, secret2]) == [
            EnvMixin._get_env_from_secret(secret2)
        ]

    def test_get_env_from_config_maps(self):
        # None
        assert EnvMixin._get_env_from_config_maps(config_maps=None) == []
        # ConfigMap with items
        config_map1 = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            is_requested=True,
        )
        # ConfigMap
        config_map2 = V1ConnectionResource(
            name="test_ref",
            is_requested=True,
        )

        assert EnvMixin._get_env_from_config_maps(
            config_maps=[config_map1, config_map2]
        ) == [EnvMixin._get_env_from_config_map(config_map2)]

    def test_get_env_from_k8s_resources(self):
        assert EnvMixin._get_env_from_k8s_resources(secrets=[], config_maps=[]) == []
        res1 = V1ConnectionResource(name="test", is_requested=True)
        res2 = V1ConnectionResource(name="test2", is_requested=True)
        expected = EnvMixin._get_env_from_secrets(secrets=[res1, res2])
        assert (
            EnvMixin._get_env_from_k8s_resources(secrets=[res1, res2], config_maps=[])
            == expected
        )
        expected = EnvMixin._get_env_from_secrets(
            secrets=[res1]
        ) + EnvMixin._get_env_from_config_maps(config_maps=[res2])
        assert (
            EnvMixin._get_env_from_k8s_resources(secrets=[res1], config_maps=[res2])
            == expected
        )
        expected = EnvMixin._get_env_from_config_maps(config_maps=[res1, res2])
        assert (
            EnvMixin._get_env_from_k8s_resources(secrets=[], config_maps=[res1, res2])
            == expected
        )

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
        env_var_names = [env_var.name for env_var in env_vars]
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
        assert len(env_vars) == 12
        env_var_names = [env_var.name for env_var in env_vars]
        assert ENV_KEYS_K8S_POD_ID in env_var_names
        assert ENV_KEYS_K8S_NAMESPACE in env_var_names
        assert ENV_KEYS_HOST in env_var_names
        assert ENV_KEYS_IS_MANAGED in env_var_names
        assert ENV_KEYS_API_VERSION in env_var_names
        assert ENV_KEYS_HEADER in env_var_names
        assert ENV_KEYS_HEADER_SERVICE in env_var_names
        assert ENV_KEYS_SECRET_KEY in env_var_names
        assert ENV_KEYS_SECRET_INTERNAL_TOKEN in env_var_names
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
        assert len(env_vars) == 12
        env_var_names = [env_var.name for env_var in env_vars]
        assert ENV_KEYS_K8S_POD_ID in env_var_names
        assert ENV_KEYS_K8S_NAMESPACE in env_var_names
        assert ENV_KEYS_HOST in env_var_names
        assert ENV_KEYS_IS_MANAGED in env_var_names
        assert ENV_KEYS_API_VERSION in env_var_names
        assert ENV_KEYS_HEADER in env_var_names
        assert ENV_KEYS_HEADER_SERVICE in env_var_names
        assert ENV_KEYS_SECRET_KEY in env_var_names
        assert ENV_KEYS_AUTH_TOKEN in env_var_names
        assert ENV_KEYS_AUTHENTICATION_TYPE in env_var_names
        assert ENV_KEYS_RUN_INSTANCE in env_var_names
