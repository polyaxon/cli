import pytest

from kubernetes import client as k8s_client

from polyaxon._flow.termination import V1Termination
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.custom_resources.setter import set_termination
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
class TestSetTermination(BaseTestCase):
    def test_pod_failure_policy_with_client_rules(self):
        termination = V1Termination(
            pod_failure_policy=k8s_schemas.V1PodFailurePolicy(
                rules=[
                    k8s_client.V1PodFailurePolicyRule(
                        action="FailJob",
                        on_exit_codes=k8s_client.V1PodFailurePolicyOnExitCodesRequirement(
                            container_name="main", operator="In", values=[42]
                        ),
                    ),
                    k8s_client.V1PodFailurePolicyRule(
                        action="Ignore",
                        on_pod_conditions=[
                            k8s_client.V1PodFailurePolicyOnPodConditionsPattern(
                                type="DisruptionTarget", status="True"
                            )
                        ],
                    ),
                ]
            )
        )

        custom_object = set_termination(custom_object={}, termination=termination)

        assert custom_object["termination"]["podFailurePolicy"] == {
            "rules": [
                {
                    "action": "FailJob",
                    "onExitCodes": {
                        "containerName": "main",
                        "operator": "In",
                        "values": [42],
                    },
                },
                {
                    "action": "Ignore",
                    "onPodConditions": [{"type": "DisruptionTarget", "status": "True"}],
                },
            ]
        }

    def test_pod_failure_policy_from_polyaxonfile(self):
        policy = {
            "rules": [
                {
                    "action": "FailJob",
                    "onExitCodes": {
                        "containerName": "main",
                        "operator": "In",
                        "values": [42],
                    },
                }
            ]
        }
        termination = V1Termination.from_dict({"podFailurePolicy": policy})

        custom_object = set_termination(custom_object={}, termination=termination)

        assert custom_object["termination"]["podFailurePolicy"] == policy
