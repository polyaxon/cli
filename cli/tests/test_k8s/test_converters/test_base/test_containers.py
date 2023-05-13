import pytest

from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.base.containers import ContainerMixin
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
class TestSanitizeContainerEnv(BaseTestCase):
    def test_sanitize_container_env_value(self):
        value = [{"foo": "bar"}]
        assert ContainerMixin._sanitize_container_env(value)[0] == {"foo": "bar"}

        value = [{"foo": 1}]
        assert ContainerMixin._sanitize_container_env(value)[0] == {"foo": "1"}

        value = [
            {
                "name": "secret-name",
                "value": True,
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "value": "true",
        }

        value = [
            {
                "name": "secret-name",
                "value": 1,
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "value": "1",
        }

        value = [
            {
                "name": "secret-name",
                "value": "test",
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "value": "test",
        }

        value = [
            {
                "name": "secret-name",
                "value": {"foo": "bar"},
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "value": '{"foo":"bar"}',
        }

        value = [{"foo": {"key": "value"}}]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "foo": {"key": "value"}
        }

    def test_sanitize_container_env_value_obj(self):
        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value=True,
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value="true",
        )

        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value=1,
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value="1",
        )

        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value="test",
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value="test",
        )

        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value={"foo": "bar"},
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value='{"foo":"bar"}',
        )

    def test_sanitize_container_env_value_from(self):
        value = [
            {
                "name": "secret-name",
                "valueFrom": {
                    "secretKeyRef": {
                        "name": "my-secret",
                        "key": "my-key",
                    }
                },
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "valueFrom": {
                "secretKeyRef": {
                    "name": "my-secret",
                    "key": "my-key",
                }
            },
        }

        value = [
            {
                "name": "secret-name",
                "valueFrom": {
                    "configKeyRef": {
                        "name": "my-secret",
                        "key": "my-key",
                    }
                },
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == {
            "name": "secret-name",
            "valueFrom": {
                "configKeyRef": {
                    "name": "my-secret",
                    "key": "my-key",
                }
            },
        }

    def test_sanitize_container_env_value_from_obj(self):
        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value_from=k8s_schemas.V1EnvVarSource(
                    config_map_key_ref=k8s_schemas.V1ConfigMapKeySelector(
                        key="my-key",
                        name="my-secret",
                    )
                ),
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value_from=k8s_schemas.V1EnvVarSource(
                config_map_key_ref=k8s_schemas.V1ConfigMapKeySelector(
                    key="my-key",
                    name="my-secret",
                )
            ),
        )

        value = [
            k8s_schemas.V1EnvVar(
                name="secret-name",
                value_from=k8s_schemas.V1EnvVarSource(
                    config_map_key_ref=k8s_schemas.V1SecretKeySelector(
                        key="my-key",
                        name="my-secret",
                    )
                ),
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[0] == k8s_schemas.V1EnvVar(
            name="secret-name",
            value_from=k8s_schemas.V1EnvVarSource(
                config_map_key_ref=k8s_schemas.V1SecretKeySelector(
                    key="my-key",
                    name="my-secret",
                )
            ),
        )
