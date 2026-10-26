import pytest

from kubernetes import client as k8s_client

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict
from polyaxon._flow.environment import V1Environment
from polyaxon._k8s import k8s_schemas
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon._vendor.k8s.serialization import sanitize_for_serialization


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

        # Add complex annotations
        config_dict["annotations"] = {
            "k8s.v1.cni.cncf.io/networks": ' [ { "name" : "test", "namespace" : "test" } ]'
        }
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

    def test_pod_security_context(self):
        config_dict = {
            "securityContext": {
                "runAsUser": 1000,
                "fsGroup": 2000,
                "fsGroupChangePolicy": "OnRootMismatch",
                "supplementalGroups": [3000],
                "sysctls": [{"name": "net.core.somaxconn", "value": "1024"}],
            }
        }
        config = V1Environment.from_dict(config_dict)

        assert isinstance(config.security_context, k8s_schemas.V1PodSecurityContext)
        assert config.security_context.fs_group == 2000
        assert config.security_context.supplemental_groups == [3000]
        assert_equal_dict(config_dict, config.to_dict())

    def test_pod_security_context_rejects_container_fields(self):
        for key, attr, value in [
            ("privileged", "privileged", True),
            ("capabilities", "capabilities", {"add": ["NET_ADMIN"]}),
            ("allowPrivilegeEscalation", "allow_privilege_escalation", False),
        ]:
            with self.subTest(key=key):
                with self.assertRaises(TypeError) as context:
                    V1Environment.from_dict(
                        {"securityContext": {"runAsUser": 1000, key: value}}
                    )
                assert attr in str(context.exception)

    def test_pod_security_context_rejects_container_security_context(self):
        for security_context in [
            k8s_schemas.V1SecurityContext(run_as_user=1000),
            k8s_client.V1SecurityContext(run_as_user=1000),
        ]:
            with self.subTest(security_context=type(security_context).__module__):
                with self.assertRaises(ValidationError) as context:
                    V1Environment(security_context=security_context)
                assert "V1PodSecurityContext" in str(context.exception)

    def test_pod_security_context_from_client(self):
        config = V1Environment(
            security_context=k8s_client.V1PodSecurityContext(
                fs_group=2000,
                seccomp_profile=k8s_client.V1SeccompProfile(
                    type="Localhost", localhost_profile="profiles/audit.json"
                ),
            )
        )

        assert isinstance(config.security_context, k8s_schemas.V1PodSecurityContext)
        assert sanitize_for_serialization(config.security_context) == {
            "fsGroup": 2000,
            "seccompProfile": {
                "type": "Localhost",
                "localhostProfile": "profiles/audit.json",
            },
        }
