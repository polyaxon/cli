import json
from mock import patch
from pathlib import Path
import pytest
import tempfile

from polyaxon._cli.components import components
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliComponent(BaseCommandTestCase):
    @patch("polyaxon._client.run.RunClient")
    @patch("polyaxon._cli.project_versions.register_project_version")
    @patch("polyaxon._cli.context.resolve_project")
    def test_register_dag_file_preserves_unresolved_path_reference(
        self, resolve_project, register_version, run_client
    ):
        resolve_project.return_value = ("owner", None, "project")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            templates = root / "templates"
            templates.mkdir()
            (templates / "job.yml").write_text(
                "kind: component\n"
                "run:\n"
                "  kind: job\n"
                "  container: {image: busybox:1.36}\n"
            )
            source = root / "dag.yml"
            source.write_text(
                "kind: component\n"
                "run:\n"
                "  kind: dag\n"
                "  operations:\n"
                "    - name: external\n"
                "      pathRef: ./templates/job.yml\n"
                "    - name: local\n"
                "      dagRef: local-template\n"
                "  components:\n"
                "    - name: local-template\n"
                "      run:\n"
                "        kind: job\n"
                "        container: {image: alpine:3.20}\n"
            )

            result = self.runner.invoke(
                components,
                ["register", "--project=owner/project", "-f", str(source)],
            )

        assert result.exit_code == 0, (result.output, result.exception)
        register_version.assert_called_once()
        submitted = json.loads(register_version.call_args.kwargs["content"])
        assert submitted["kind"] == "component"
        assert submitted["run"]["operations"][0]["pathRef"] == "./templates/job.yml"
        assert not submitted["run"]["operations"][0].get("component")
        assert submitted["run"]["operations"][1]["dagRef"] == "local-template"
        local_component = submitted["run"]["components"][0]
        assert local_component["run"]["container"]["image"] == "alpine:3.20"
        run_client.assert_not_called()

    @patch("polyaxon._sdk.api.projects_v1_api.ProjectsV1Api.create_version")
    @patch("polyaxon._sdk.api.projects_v1_api.ProjectsV1Api.get_version")
    def test_create_component(self, get_version, create_component):
        self.runner.invoke(components, ["push"])
        assert create_component.call_count == 0
        assert get_version.call_count == 0
        self.runner.invoke(components, ["push", "--name=owner/foo"])
        assert get_version.call_count == 0
        assert create_component.call_count == 0

    @patch("polyaxon._sdk.api.projects_v1_api.ProjectsV1Api.list_versions")
    def test_list_components(self, list_components):
        self.runner.invoke(components, ["ls", "--project=owner/foo"])
        assert list_components.call_count == 1

    @patch("polyaxon._sdk.api.projects_v1_api.ProjectsV1Api.get_version")
    def test_get_components(self, get_components):
        self.runner.invoke(components, ["get", "-p", "admin/foo"])
        assert get_components.call_count == 1

    @patch("polyaxon._sdk.api.projects_v1_api.ProjectsV1Api.patch_version")
    def test_update_components(self, update_components):
        self.runner.invoke(
            components, ["update", "-p", "admin/foo", "--description=foo"]
        )
        assert update_components.call_count == 1

    @patch("polyaxon._sdk.api.projects_v1_api.ProjectsV1Api.create_version_stage")
    def test_update_artifact_stage(self, stage_component):
        self.runner.invoke(
            components,
            ["stage", "-p", "admin/foo", "-to", "production", "--reason=foo"],
        )
        assert stage_component.call_count == 1
