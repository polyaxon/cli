import pytest

from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.base.containers import ContainerMixin
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
class TestPatchContainer(BaseTestCase):
    def test_patch_container_normalizes_and_dedupes_ports(self):
        existing = k8s_schemas.V1ContainerPort(
            name="sandbox", container_port=9090
        )
        http = k8s_schemas.V1ContainerPort(name="http", container_port=8080)
        container = ContainerMixin._patch_container(
            container=k8s_schemas.V1Container(name="main", ports=[existing]),
            ports=[
                9090,
                http,
                {"name": "http-dup", "containerPort": 8080},
                {"name": "admin", "containerPort": 8081},
            ],
        )

        assert container.ports == [
            existing,
            http,
            k8s_schemas.V1ContainerPort(name="admin", container_port=8081),
        ]


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
