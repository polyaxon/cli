import json
from mock import patch
from pathlib import Path
import pytest
import tempfile

from polyaxon._cli.components import components
from polyaxon._sdk.schemas.v1_project_version import V1ProjectVersion
from polyaxon.exceptions import ApiException
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliComponent(BaseCommandTestCase):
    @patch("polyaxon._sdk.api.runs_v1_api.RunsV1Api.create_run")
    @patch("polyaxon._cli.project_versions.get_dashboard_url", return_value="hub-url")
    @patch("polyaxon._cli.context.resolve_project")
    @patch(
        "polyaxon._sdk.api.projects_v1_api.ProjectsV1Api.get_version",
        side_effect=ApiException(status=404),
    )
    @patch("polyaxon._sdk.api.projects_v1_api.ProjectsV1Api.create_version")
    def test_register_shared_file_preserves_native_fields(
        self, create_version, get_version, resolve_project, dashboard, create_run
    ):
        resolve_project.return_value = ("owner", None, "project")
        create_version.return_value = V1ProjectVersion(name="v1")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "job.yml"
            for kind in (None, "component", "operation"):
                with self.subTest(kind=kind):
                    create_version.reset_mock()
                    content = {
                        "strictParams": True,
                        "inputs": [{"name": "count", "type": "int"}],
                        "params": {"count": 3},
                        "presets": ["team-defaults"],
                        "matrix": {
                            "kind": "grid",
                            "params": {"count": {"kind": "choice", "value": [1, 2]}},
                        },
                        "run": {
                            "kind": "job",
                            "container": {
                                "image": "busybox:1.36",
                                "resources": {"limits": {"nvidia.com/gpu": 1}},
                            },
                        },
                    }
                    if kind:
                        content["kind"] = kind
                    source.write_text(json.dumps(content))

                    result = self.runner.invoke(
                        components,
                        [
                            "register",
                            "--project=owner/project",
                            "--version=v1",
                            "-f",
                            str(source),
                        ],
                    )

                    assert result.exit_code == 0, (result.output, result.exception)
                    create_version.assert_called_once()
                    assert create_version.call_args.args == (
                        "owner",
                        "project",
                        "component",
                    )
                    body = create_version.call_args.kwargs["body"]
                    assert body.name == "v1"
                    assert isinstance(body.content, str)
                    submitted = json.loads(body.content)
                    assert submitted.get("kind") == kind
                    assert "component" not in submitted
                    assert submitted["strictParams"] is True
                    assert submitted["params"] == {"count": {"value": 3}}
                    for field in ("inputs", "presets", "matrix", "run"):
                        assert submitted[field] == content[field]
                    create_run.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    @patch("polyaxon._cli.project_versions.register_project_version")
    @patch("polyaxon._cli.context.resolve_project")
    def test_register_preserves_explicit_nulls(
        self, resolve_project, register_version, run_client
    ):
        resolve_project.return_value = ("owner", None, "project")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "job.yml"
            for kind in (None, "component", "operation"):
                with self.subTest(kind=kind):
                    register_version.reset_mock()
                    content = {
                        "component": {
                            "schedule": {"kind": "cron", "cron": "0 * * * *"},
                            "matrix": {
                                "kind": "grid",
                                "params": {
                                    "count": {"kind": "choice", "value": [1, 2]}
                                },
                            },
                            "run": {
                                "kind": "job",
                                "container": {"image": "busybox:1.36"},
                            },
                        },
                        "schedule": None,
                        "matrix": None,
                    }
                    if kind:
                        content["kind"] = kind
                    source.write_text(json.dumps(content))

                    result = self.runner.invoke(
                        components,
                        [
                            "register",
                            "--project=owner/project",
                            "--version=v1",
                            "-f",
                            str(source),
                        ],
                    )

                    assert result.exit_code == 0, (result.output, result.exception)
                    register_version.assert_called_once()
                    submitted = register_version.call_args.kwargs["content"]
                    assert json.loads(submitted) == content
                    run_client.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    @patch("polyaxon._cli.project_versions.register_project_version")
    @patch("polyaxon._cli.context.resolve_project")
    def test_register_dag_file_collects_relative_path_reference(
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
        external = submitted["run"]["operations"][0]["component"]
        assert external["run"]["container"]["image"] == "busybox:1.36"
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
