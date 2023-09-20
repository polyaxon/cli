import pytest

from polyaxon._docker import docker_types
from polyaxon._docker.converter.base.containers import ContainerMixin
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.docker_mark
class TestSanitizeContainerEnv(BaseTestCase):
    def test_sanitize_container_env_value(self):
        value = [{"foo": "bar"}]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(__root__={"foo": "bar"})

        value = [{"foo": 1}]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(__root__={"foo": "1"})

        value = [
            {
                "name": "secret-name",
                "value": True,
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__={
                "name": "secret-name",
                "value": "true",
            }
        )

        value = [
            {
                "name": "secret-name",
                "value": 1,
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__={
                "name": "secret-name",
                "value": "1",
            }
        )

        value = [
            {
                "name": "secret-name",
                "value": "test",
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__={
                "name": "secret-name",
                "value": "test",
            }
        )

        value = [
            {
                "name": "secret-name",
                "value": {"foo": "bar"},
            },
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__={
                "name": "secret-name",
                "value": '{"foo":"bar"}',
            }
        )

        value = [{"foo": {"key": "value"}}]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(__root__={"foo": '{"key":"value"}'})

    def test_sanitize_container_env_value_obj_from_dict(self):
        value = [
            dict(
                name="secret-name",
                value=True,
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__=dict(
                name="secret-name",
                value="true",
            )
        )

        value = [
            dict(
                name="secret-name",
                value=1,
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__=dict(
                name="secret-name",
                value="1",
            )
        )

        value = [
            dict(
                name="secret-name",
                value="test",
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__=dict(
                name="secret-name",
                value="test",
            )
        )

        value = [
            dict(
                name="secret-name",
                value={"foo": "bar"},
            ),
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__=dict(
                name="secret-name",
                value='{"foo":"bar"}',
            )
        )

    def test_sanitize_container_env_value_obj_from_tuple(self):
        value = [
            ("secret-name", True),
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__=(
                "secret-name",
                "true",
            )
        )

        value = [
            ("secret-name", 1),
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(__root__=("secret-name", "1"))

        value = [
            ("secret-name", "test"),
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__=(
                "secret-name",
                "test",
            )
        )

        value = [
            ("secret-name", {"foo": "bar"}),
        ]
        assert ContainerMixin._sanitize_container_env(value)[
            0
        ] == docker_types.V1EnvVar(
            __root__=(
                "secret-name",
                '{"foo":"bar"}',
            )
        )
