import os
import pytest
import re

from kubernetes import client as k8s_client

from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon._vendor import k8s as vendored_k8s


PYDANTIC_CLIENT = hasattr(k8s_client.V1EnvVar, "model_fields")


@pytest.mark.k8s_mark
class TestK8sValidation(BaseTestCase):
    def test_schemas_are_vendored(self):
        for name, cls in vars(k8s_schemas).items():
            if name.startswith("V1"):
                assert cls.__module__.startswith("polyaxon._vendor.k8s.models"), name

    def test_vendored_modules_do_not_import_kubernetes(self):
        paths = [k8s_schemas.__file__]
        for dirpath, _, filenames in os.walk(os.path.dirname(vendored_k8s.__file__)):
            paths += [os.path.join(dirpath, f) for f in filenames if f.endswith(".py")]
        pattern = re.compile(r"^\s*(?:import|from)\s+(?:kubernetes|six)\b", re.M)
        for path in paths:
            with open(path) as f:
                assert not pattern.search(f.read()), path

    def test_converts_client_models_at_any_depth(self):
        lifecycle = k8s_client.V1Lifecycle()
        container = k8s_validation.validate_k8s_container(
            k8s_client.V1Container(
                name="main",
                resources=k8s_client.V1ResourceRequirements(requests={"cpu": "1"}),
                ports=[k8s_client.V1ContainerPort(container_port=8080)],
                env=[k8s_client.V1EnvVar(name="FOO", value="bar")],
                lifecycle=lifecycle,
            )
        )

        assert isinstance(container, k8s_schemas.V1Container)
        assert isinstance(container.resources, k8s_schemas.V1ResourceRequirements)
        assert container.resources.requests == {"cpu": "1"}
        assert isinstance(container.ports[0], k8s_schemas.V1ContainerPort)
        assert container.ports[0].container_port == 8080
        assert isinstance(container.env[0], k8s_schemas.V1EnvVar)
        assert container.env[0].value == "bar"
        # Client models without a vendored version are kept as is
        assert container.lifecycle is lifecycle

    def test_converts_client_models_in_dicts_and_vendored_models(self):
        container = k8s_validation.validate_k8s_container(
            {"name": "main", "env": [k8s_client.V1EnvVar(name="FOO", value="bar")]}
        )
        assert isinstance(container.env[0], k8s_schemas.V1EnvVar)

        container = k8s_schemas.V1Container(
            name="main", env=[k8s_client.V1EnvVar(name="FOO", value="bar")]
        )
        assert k8s_validation.validate_k8s_container(container) is container
        assert isinstance(container.env[0], k8s_schemas.V1EnvVar)

    def test_keeps_values_without_client_models(self):
        env = [{"name": "FOO", "value": "bar"}]
        container = k8s_schemas.V1Container(name="main", env=env)

        assert k8s_validation.validate_k8s_container(container) is container
        assert container.env is env

    @pytest.mark.skipif(PYDANTIC_CLIENT, reason="Only python-legacy client models")
    def test_keeps_client_validation_configuration(self):
        configuration = k8s_client.Configuration()
        configuration.client_side_validation = False
        env_var = k8s_validation.validate_k8s_env_var(
            k8s_client.V1EnvVar(name=None, local_vars_configuration=configuration)
        )

        assert isinstance(env_var, k8s_schemas.V1EnvVar)
        assert env_var.name is None

    def test_rejects_unsupported_client_fields(self):
        class V1EnvVar:
            __module__ = "kubernetes.client.models.v1_env_var"
            openapi_types = {"name": "str", "value": "str", "new_field": "str"}

            def __init__(self):
                self.name = "FOO"
                self.value = "bar"
                self.new_field = "value"

        with pytest.raises(ValueError):
            k8s_validation.validate_k8s_env_var(V1EnvVar())
