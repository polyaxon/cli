import pytest

from clipped.utils.assertions import assert_equal_dict
from polyaxon._k8s import k8s_schemas
from kubernetes import client as k8s_client

from polyaxon._flow.termination import (
    V1Termination,
    V1Culling,
    V1ActivityProbe,
)
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.termination_mark
class TestV1Terminations(BaseTestCase):
    def test_termination_config(self):
        config_dict = {}
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        config_dict["maxRetries"] = "{{ fs }}"
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add max_retries
        config_dict["maxRetries"] = 4
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add timeout
        config_dict["timeout"] = 4
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add ttl
        config_dict["ttl"] = 40
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

    def test_culling_config(self):
        # Empty culling
        config_dict = {}
        config = V1Culling.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # With timeout
        config_dict = {"timeout": 3600}
        config = V1Culling.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())
        assert config.timeout == 3600

    def test_activity_probe_config(self):
        # With http probe
        config_dict = {"http": {"path": "/api/status", "port": 8888}}
        config = V1ActivityProbe.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())
        assert config.http is not None
        assert config.http.path == "/api/status"
        assert config.http.port == 8888

        # With exec probe
        config_dict = {"exec": {"command": ["bash", "-c", "check-activity.sh"]}}
        config = V1ActivityProbe.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())
        assert config.var_exec is not None
        assert config.var_exec.command == ["bash", "-c", "check-activity.sh"]

    def test_termination_with_culling_and_probe(self):
        config_dict = {
            "maxRetries": 3,
            "timeout": 86400,
            "ttl": 1000,
            "culling": {"timeout": 3600},
            "probe": {"http": {"path": "/api/status", "port": 8888}},
        }
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Verify nested structures
        assert config.max_retries == 3
        assert config.timeout == 86400
        assert config.ttl == 1000
        assert config.culling is not None
        assert config.culling.timeout == 3600
        assert config.probe is not None
        assert config.probe.http is not None
        assert config.probe.http.path == "/api/status"
        assert config.probe.http.port == 8888

    def test_termination_with_exec_probe(self):
        config_dict = {
            "culling": {"timeout": 7200},
            "probe": {
                "exec": {"command": ["bash", "-c", "/scripts/check-activity.sh"]}
            },
        }
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Verify nested structures
        assert config.culling is not None
        assert config.culling.timeout == 7200
        assert config.probe is not None
        assert config.probe.var_exec is not None
        assert config.probe.var_exec.command == [
            "bash",
            "-c",
            "/scripts/check-activity.sh",
        ]

    def test_pod_failure_policy(self):
        # Test instantiating k8s_schemas.V1PodFailurePolicy directly
        policy = k8s_schemas.V1PodFailurePolicy(
            rules=[
                k8s_client.V1PodFailurePolicyRule(
                    action="FailJob",
                    on_exit_codes=k8s_client.V1PodFailurePolicyOnExitCodesRequirement(
                        container_name="main",
                        operator="In",
                        values=[42],
                    ),
                ),
                k8s_client.V1PodFailurePolicyRule(
                    action="Ignore",
                    on_pod_conditions=[
                        k8s_client.V1PodFailurePolicyOnPodConditionsPattern(
                            type="DisruptionTarget",
                            status="True",
                        )
                    ],
                ),
            ],
        )
        assert policy is not None
        assert len(policy.rules) == 2
        assert policy.rules[0].action == "FailJob"
        assert policy.rules[0].on_exit_codes.operator == "In"
        assert policy.rules[1].action == "Ignore"

    def test_termination_with_pod_failure_policy(self):
        config_dict = {
            "maxRetries": 3,
            "timeout": 3600,
            "podFailurePolicy": {
                "rules": [
                    {
                        "action": "FailJob",
                        "onExitCodes": {
                            "operator": "In",
                            "values": [42],
                        },
                    },
                    {
                        "action": "Ignore",
                        "onPodConditions": [
                            {"type": "DisruptionTarget", "status": "True"},
                        ],
                    },
                ],
            },
        }
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Verify basic structure
        assert config.max_retries == 3
        assert config.timeout == 3600
        assert config.pod_failure_policy is not None
        assert len(config.pod_failure_policy.rules) == 2

        # Verify rules structure (nested structures remain as dicts with camelCase keys)
        rule1 = config.pod_failure_policy.rules[0]
        rule2 = config.pod_failure_policy.rules[1]
        assert rule1["action"] == "FailJob"
        assert rule1["onExitCodes"] is not None
        assert rule1["onExitCodes"]["operator"] == "In"
        assert rule1["onExitCodes"]["values"] == [42]
        assert rule2["action"] == "Ignore"
        assert rule2["onPodConditions"] is not None
        assert len(rule2["onPodConditions"]) == 1
        assert rule2["onPodConditions"][0]["type"] == "DisruptionTarget"
