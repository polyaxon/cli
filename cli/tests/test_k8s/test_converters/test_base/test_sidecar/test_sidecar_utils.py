import pytest

from polyaxon._auxiliaries import get_sidecar_resources
from polyaxon._env_vars.keys import ENV_KEYS_ARTIFACTS_STORE_NAME, ENV_KEYS_CONTAINER_ID
from polyaxon._k8s import k8s_schemas
from tests.test_k8s.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestSidecarContainer(BaseConverterTest):
    def test_get_sidecar_env_vars(self):
        sidecar_env_vars = self.converter._get_sidecar_env_vars(
            env_vars=None, container_id="foo", artifacts_store_name="name"
        )

        assert sidecar_env_vars == [
            self.converter._get_env_var(name=ENV_KEYS_CONTAINER_ID, value="foo"),
            self.converter._get_env_var(
                name=ENV_KEYS_ARTIFACTS_STORE_NAME, value="name"
            ),
        ]

        # Initial env vars
        env_vars = [
            self.converter._get_env_var(name="key1", value="value1"),
            self.converter._get_env_var(name="key2", value="value2"),
        ]
        sidecar_env_vars = self.converter._get_sidecar_env_vars(
            env_vars=env_vars, container_id="foo", artifacts_store_name="name"
        )

        assert sidecar_env_vars == env_vars + [
            self.converter._get_env_var(name=ENV_KEYS_CONTAINER_ID, value="foo"),
            self.converter._get_env_var(
                name=ENV_KEYS_ARTIFACTS_STORE_NAME, value="name"
            ),
        ]

        # Outputs Path
        sidecar_env_vars = self.converter._get_sidecar_env_vars(
            env_vars=None, container_id="foo", artifacts_store_name="name"
        )

        assert sidecar_env_vars == [
            self.converter._get_env_var(name=ENV_KEYS_CONTAINER_ID, value="foo"),
            self.converter._get_env_var(
                name=ENV_KEYS_ARTIFACTS_STORE_NAME, value="name"
            ),
        ]

    def test_get_sidecar_resources(self):
        assert get_sidecar_resources() == k8s_schemas.V1ResourceRequirements(
            limits={"cpu": "1", "memory": "500Mi"},
            requests={"cpu": "0.1", "memory": "60Mi"},
        )

    def test_get_sidecar_args(self):
        assert self.converter._get_sidecar_args(
            container_id="job.2",
            sleep_interval=23,
            sync_interval=2,
            monitor_logs=False,
            monitor_spec=False,
        ) == ["--container-id=job.2", "--sleep-interval=23", "--sync-interval=2"]
        assert self.converter._get_sidecar_args(
            container_id="job.2",
            sleep_interval=23,
            sync_interval=2,
            monitor_logs=None,
            monitor_spec=None,
        ) == [
            "--container-id=job.2",
            "--sleep-interval=23",
            "--sync-interval=2",
            "--monitor-logs",
            "--monitor-spec",
        ]
        assert self.converter._get_sidecar_args(
            container_id="job.2",
            sleep_interval=23,
            sync_interval=2,
            monitor_logs=True,
            monitor_spec=True,
        ) == [
            "--container-id=job.2",
            "--sleep-interval=23",
            "--sync-interval=2",
            "--monitor-logs",
            "--monitor-spec",
        ]
