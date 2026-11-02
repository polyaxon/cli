import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.json import orjson_dumps
from polyaxon._connections import (
    V1BucketConnection,
    V1ConnectionKind,
    V1ConnectionResource,
)
from polyaxon._env_vars.keys import (
    ENV_KEYS_AGENT_ARTIFACTS_STORE,
    ENV_KEYS_AGENT_CONNECTIONS,
    ENV_KEYS_AGENT_DEFAULT_SCHEDULING,
    ENV_KEYS_K8S_NAMESPACE,
)
from polyaxon._k8s import k8s_schemas
from polyaxon._schemas.agent import AgentConfig
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.schemas_mark
class TestAgentConfig(BaseTestCase):
    def test_agent_config(self):
        config_dict = {ENV_KEYS_AGENT_ARTIFACTS_STORE: 12}
        with self.assertRaises(ValidationError):
            AgentConfig.from_dict(config_dict)

        config_dict = {ENV_KEYS_AGENT_ARTIFACTS_STORE: "some"}
        with self.assertRaises(ValidationError):
            AgentConfig.from_dict(config_dict)

        config_dict = {
            ENV_KEYS_K8S_NAMESPACE: "foo",
            ENV_KEYS_AGENT_ARTIFACTS_STORE: {
                "name": "some",
                "kind": V1ConnectionKind.GCS,
                "schema": V1BucketConnection(bucket="gs://test").to_dict(),
            },
        }
        config = AgentConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {
            ENV_KEYS_K8S_NAMESPACE: "foo",
            ENV_KEYS_AGENT_ARTIFACTS_STORE: "some",
            ENV_KEYS_AGENT_CONNECTIONS: [
                {
                    "name": "some",
                    "kind": V1ConnectionKind.GCS,
                    "schema": V1BucketConnection(bucket="gs://test").to_dict(),
                    "secretResource": "some",
                }
            ],
        }
        with self.assertRaises(ValidationError):
            AgentConfig.from_dict(config_dict)

        config_dict = {
            ENV_KEYS_K8S_NAMESPACE: "foo",
            ENV_KEYS_AGENT_ARTIFACTS_STORE: {
                "name": "test",
                "kind": V1ConnectionKind.GCS,
                "schema": V1BucketConnection(bucket="gs://test").to_dict(),
                "secret": V1ConnectionResource(name="some").to_dict(),
            },
            ENV_KEYS_AGENT_CONNECTIONS: [
                {
                    "name": "some",
                    "kind": V1ConnectionKind.GCS,
                    "schema": V1BucketConnection(bucket="gs://test").to_dict(),
                    "secret": V1ConnectionResource(name="some").to_dict(),
                },
                {
                    "name": "slack",
                    "kind": V1ConnectionKind.SLACK,
                    "secret": V1ConnectionResource(name="some").to_dict(),
                },
            ],
        }
        config = AgentConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

    def test_agent_config_from_str_envs(self):
        config_dict = {
            ENV_KEYS_K8S_NAMESPACE: "foo",
            ENV_KEYS_AGENT_ARTIFACTS_STORE: orjson_dumps(
                {
                    "name": "test1",
                    "kind": V1ConnectionKind.GCS,
                    "schema": V1BucketConnection(bucket="gs://test").to_dict(),
                    "secret": V1ConnectionResource(name="some").to_dict(),
                }
            ),
            ENV_KEYS_AGENT_CONNECTIONS: orjson_dumps(
                [
                    {
                        "name": "test2",
                        "kind": V1ConnectionKind.GCS,
                        "schema": V1BucketConnection(bucket="gs://test").to_dict(),
                        "secret": V1ConnectionResource(name="some").to_dict(),
                    },
                    {
                        "name": "slack",
                        "kind": V1ConnectionKind.SLACK,
                        "secret": V1ConnectionResource(name="some").to_dict(),
                    },
                ]
            ),
        }

        config = AgentConfig.from_dict(config_dict)
        assert len(config.secrets) == 1
        assert len(config.to_light_dict()[ENV_KEYS_AGENT_CONNECTIONS]) == 2

    def test_agent_config_default_scheduling_security_context(self):
        store = {
            "name": "test",
            "kind": V1ConnectionKind.GCS,
            "schema": V1BucketConnection(bucket="gs://test").to_dict(),
            "secret": V1ConnectionResource(name="some").to_dict(),
        }
        scheduling = {
            "nodeSelector": {"polyaxon": "core"},
            "securityContext": {
                "runAsUser": 2222,
                "runAsGroup": 2222,
                "fsGroup": 2222,
                "fsGroupChangePolicy": "OnRootMismatch",
            },
        }
        config = AgentConfig.from_dict(
            {
                ENV_KEYS_K8S_NAMESPACE: "foo",
                ENV_KEYS_AGENT_ARTIFACTS_STORE: orjson_dumps(store),
                ENV_KEYS_AGENT_DEFAULT_SCHEDULING: orjson_dumps(scheduling),
            }
        )

        security_context = config.default_scheduling.security_context
        assert isinstance(security_context, k8s_schemas.V1PodSecurityContext)
        assert security_context.run_as_user == 2222
        assert security_context.fs_group_change_policy == "OnRootMismatch"
        assert config.default_scheduling.node_selector == {"polyaxon": "core"}

        # The agent passes its config as JSON when converting runs
        restored = AgentConfig.read(config.to_json())
        assert restored.default_scheduling.to_dict() == scheduling

    def test_agent_config_default_scheduling_without_security_context(self):
        store = {
            "name": "test",
            "kind": V1ConnectionKind.GCS,
            "schema": V1BucketConnection(bucket="gs://test").to_dict(),
            "secret": V1ConnectionResource(name="some").to_dict(),
        }
        scheduling = {"nodeSelector": {"polyaxon": "core"}}
        config = AgentConfig.from_dict(
            {
                ENV_KEYS_K8S_NAMESPACE: "foo",
                ENV_KEYS_AGENT_ARTIFACTS_STORE: orjson_dumps(store),
                ENV_KEYS_AGENT_DEFAULT_SCHEDULING: orjson_dumps(scheduling),
            }
        )

        assert config.default_scheduling.security_context is None
        assert config.default_scheduling.to_dict() == scheduling
