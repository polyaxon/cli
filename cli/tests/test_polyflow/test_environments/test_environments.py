import pytest

from clipped.utils.assertions import assert_equal_dict

from polyaxon._flow.environment import V1Environment
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.environment_mark
class TestEnvironmentsConfigs(BaseTestCase):
    def test_environment_config(self):
        # Resources
        config_dict = {"labels": {"foo": "bar"}}
        config = V1Environment.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add node selectors
        config_dict["nodeSelector"] = {"polyaxon.com": "master"}

        config = V1Environment.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add affinity
        config_dict["affinity"] = {
            "nodeAffinity": {"requiredDuringSchedulingIgnoredDuringExecution": {}}
        }

        config = V1Environment.from_dict(config_dict)
        assert config.affinity.node_affinity == {
            "requiredDuringSchedulingIgnoredDuringExecution": {}
        }
        assert_equal_dict(config_dict, config.to_dict())

        # Add labels
        config_dict["labels"] = {"foo": "bar"}

        config = V1Environment.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add annotations
        config_dict["annotations"] = {"foo": "bar"}

        config = V1Environment.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add toleration
        config_dict["tolerations"] = [{"key": "key", "operator": "Exists"}]
        config = V1Environment.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add service_account
        config_dict["serviceAccountName"] = "service_account_name"
        config = V1Environment.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add image_pull_secrets
        config_dict["imagePullSecrets"] = ["secret1", "secret2"]
        config = V1Environment.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add security context per job
        config_dict["securityContext"] = {"runAsUser": 1000, "runAsGroup": 3000}
        config = V1Environment.from_dict(config_dict)
        assert config.security_context.run_as_user == 1000
        assert config.security_context.run_as_group == 3000
        assert_equal_dict(config_dict, config.to_dict())

        # Add restart_policy
        config_dict["restartPolicy"] = "Never"
        config = V1Environment.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add host namespaces
        config_dict["hostNetwork"] = True
        config_dict["hostPID"] = True
        config = V1Environment.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())
