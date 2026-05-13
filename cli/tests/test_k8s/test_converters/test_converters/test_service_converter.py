import pytest
from unittest.mock import patch

from polyaxon._auxiliaries.init import V1PolyaxonInitContainer
from polyaxon._env_vars.keys import (
    ENV_KEYS_SANDBOX_TOKEN,
    ENV_KEYS_SECRET_INTERNAL_TOKEN,
)
from polyaxon._flow import V1CompiledOperation, V1Plugins, V1Service
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.converters.service import ServiceConverter
from polyaxon._sandbox.auth import derive_sandbox_token
from polyaxon._sandbox.constants import SANDBOX_BOOTSTRAP_PATH, SANDBOX_PORT
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.converter_mark
class TestServiceConverter(BaseTestCase):
    SET_AGENT_SETTINGS = True

    def setUp(self):
        super().setUp()
        self.converter = ServiceConverter(
            owner_name="owner-name",
            project_name="project-name",
            run_name="run-name",
            run_uuid="run_uuid",
            polyaxon_init=V1PolyaxonInitContainer(image="foo/init", image_tag=""),
        )

    @staticmethod
    def get_sandbox_plugins():
        return V1Plugins(
            sandbox=True,
            auth=False,
            docker=False,
            shm=False,
            tmux=False,
            collect_artifacts=False,
            collect_logs=False,
            collect_resources=False,
            mount_artifacts_store=False,
        )

    def test_get_resource_with_sandbox_only(self):
        compiled_operation = V1CompiledOperation(
            plugins=self.get_sandbox_plugins(),
            run=V1Service(
                container=k8s_schemas.V1Container(
                    name="main",
                    image="python:3.12",
                ),
            ),
        )

        with patch.dict(
            "os.environ", {ENV_KEYS_SECRET_INTERNAL_TOKEN: "internal-token"}
        ):
            resource = self.converter.get_resource(
                compiled_operation=compiled_operation,
                artifacts_store=None,
                connection_by_names={},
                secrets=[],
                config_maps=[],
            )

        service_spec = resource["serviceSpec"]
        template = service_spec["template"]
        main_container = template.spec.containers[0]
        env_by_name = {e.name: e for e in main_container.env}

        assert service_spec["ports"] == [SANDBOX_PORT]
        assert main_container.command == [SANDBOX_BOOTSTRAP_PATH]
        assert main_container.args == []
        assert [p.container_port for p in main_container.ports] == [SANDBOX_PORT]
        assert env_by_name[ENV_KEYS_SANDBOX_TOKEN].value == derive_sandbox_token(
            "internal-token", self.converter.run_uuid
        )
        assert len(template.spec.init_containers) == 1
        assert "/usr/bin/plx-exec" in template.spec.init_containers[0].command[-1]

    def test_get_resource_with_sandbox_port_dedupe(self):
        compiled_operation = V1CompiledOperation(
            plugins=self.get_sandbox_plugins(),
            run=V1Service(
                container=k8s_schemas.V1Container(
                    name="main",
                    image="python:3.12",
                    command=["python"],
                ),
                ports=[SANDBOX_PORT],
            ),
        )

        with patch.dict(
            "os.environ", {ENV_KEYS_SECRET_INTERNAL_TOKEN: "internal-token"}
        ):
            resource = self.converter.get_resource(
                compiled_operation=compiled_operation,
                artifacts_store=None,
                connection_by_names={},
                secrets=[],
                config_maps=[],
            )

        service_spec = resource["serviceSpec"]
        main_container = service_spec["template"].spec.containers[0]

        assert service_spec["ports"] == [SANDBOX_PORT]
        assert [p.container_port for p in main_container.ports] == [SANDBOX_PORT]
