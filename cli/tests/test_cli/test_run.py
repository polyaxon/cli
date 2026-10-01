import json
from mock import patch
import os
from pathlib import Path
import pytest
import tempfile
from types import SimpleNamespace

from polyaxon._cli.check import check
from polyaxon._cli.run import run
from polyaxon._client.run import RunClient
from polyaxon._flow.run.enums import V1RunPending
from polyaxon._polyaxonfile.specs import OperationSpecification
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_run_settings import V1RunSettings
from polyaxon._utils.cli_constants import SYMLINK_MODES
from polyaxon.exceptions import ApiException
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliRun(BaseCommandTestCase):
    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._sdk.api.runs_v1_api.RunsV1Api.create_run")
    def test_explicit_null_run_is_rejected_before_submission(
        self, create_run, resolve_project
    ):
        resolve_project.return_value = ("owner", None, "project")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cleared.yaml"
            for kind in (None, "component", "operation"):
                prefix = "kind: {}\n".format(kind) if kind else ""
                source.write_text(
                    prefix + "component:\n"
                    "  run: {kind: job, container: {image: busybox:1.36}}\n"
                    "run: null\n"
                )
                for command, args in (
                    (check, ["-f", str(source)]),
                    (run, ["--project=owner/project", "-f", str(source)]),
                ):
                    with self.subTest(kind=kind, command=command.name):
                        result = self.runner.invoke(command, args)

                        assert result.exit_code == 1, (result.output, result.exception)
                        output = " ".join(result.output.lower().split())
                        assert "resolved polyaxonfile has no run" in output
                        create_run.assert_not_called()

    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._sdk.api.runs_v1_api.RunsV1Api.create_run")
    def test_python_component_with_null_run_is_rejected_before_submission(
        self, create_run, resolve_project
    ):
        resolve_project.return_value = ("owner", None, "project")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "cleared_component.py"
            source.write_text(
                "from polyaxon.schemas import V1Component, V1Job\n"
                "from polyaxon._k8s.k8s_schemas import V1Container\n"
                "component = V1Component(\n"
                "    component=V1Component(\n"
                "        run=V1Job(container=V1Container(image='busybox:1.36')),\n"
                "    ),\n"
                "    run=None,\n"
                ")\n"
            )
            for command, args in (
                (check, ["-pm", "{}:component".format(source)]),
                (
                    run,
                    ["--project=owner/project", "-pm", "{}:component".format(source)],
                ),
            ):
                with self.subTest(command=command.name):
                    result = self.runner.invoke(command, args)

                    assert result.exit_code == 1, (result.output, result.exception)
                    output = " ".join(result.output.lower().split())
                    assert "resolved polyaxonfile has no run" in output
                    create_run.assert_not_called()

    @patch("polyaxon._utils.cache.cache")
    @patch("polyaxon._cli.dashboard.get_dashboard_url", return_value="run-url")
    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._sdk.api.runs_v1_api.RunsV1Api.create_run")
    def test_run_preserves_authored_nulls_in_submitted_content(
        self, create_run, resolve_project, dashboard, cache
    ):
        resolve_project.return_value = ("owner", None, "project")
        create_run.return_value = V1Run(
            uuid="8aac02e3a62a4f0aaa257c59da5eab80",
            name="shared",
            settings=V1RunSettings(),
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "nulls.yaml"
            for strategy in ("pre_merge", "isnull"):
                with self.subTest(strategy=strategy):
                    create_run.reset_mock()
                    source.write_text(
                        "component:\n"
                        "  queue: base\n"
                        "  run: {kind: job, container: {image: busybox:1.36}}\n"
                        "queue: null\n"
                        "termination: null\n"
                        "run: null\n"
                        f"patchStrategy: {strategy}\n"
                    )

                    result = self.runner.invoke(
                        run, ["--project=owner/project", "-f", str(source)]
                    )

                    assert result.exit_code == 0, (result.output, result.exception)
                    create_run.assert_called_once()
                    submitted = json.loads(create_run.call_args.kwargs["body"].content)
                    assert submitted["run"] is None
                    assert submitted["queue"] is None
                    assert submitted["termination"] is None
                    assert "version" not in submitted
                    compiled = OperationSpecification.compile_operation(
                        OperationSpecification.read(submitted)
                    )
                    assert compiled.queue == "base"
                    assert compiled.run.container.image == "busybox:1.36"

    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._sdk.api.runs_v1_api.RunsV1Api.create_run")
    def test_run_shared_file_reports_server_version_error(
        self, create_run, resolve_project
    ):
        resolve_project.return_value = ("owner", None, "project")
        error = ApiException(status=400, reason="Bad Request")
        error.body = '["The Polyaxonfile `version` must be specified."]'
        create_run.side_effect = error
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "job.yaml"
            source.write_text("run: {kind: job, container: {image: busybox:1.36}}\n")

            result = self.runner.invoke(
                run, ["--project=owner/project", "-f", str(source)]
            )

        assert result.exit_code == 1, (result.output, result.exception)
        assert "The Polyaxonfile `version` must be specified." in result.output
        create_run.assert_called_once()
        submitted = json.loads(create_run.call_args.kwargs["body"].content)
        assert "version" not in submitted
        assert "component" not in submitted
        assert submitted["run"]["container"]["image"] == "busybox:1.36"

    @patch("polyaxon._utils.cache.cache")
    @patch("polyaxon._cli.dashboard.get_dashboard_url", return_value="run-url")
    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._sdk.api.runs_v1_api.RunsV1Api.create_run")
    def test_run_python_component_preserves_explicit_schema_version(
        self, create_run, resolve_project, dashboard, cache
    ):
        resolve_project.return_value = ("owner", None, "project")
        create_run.return_value = V1Run(
            uuid="8aac02e3a62a4f0aaa257c59da5eab80",
            name="typed",
            settings=V1RunSettings(),
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "typed.py"
            source.write_text(
                "from polyaxon.schemas import V1Component, V1IO, V1Job\n"
                "from polyaxon._k8s.k8s_schemas import V1Container\n"
                "component = V1Component(\n"
                "    version=1.1,\n"
                "    inputs=[V1IO(name='epochs', type='int')],\n"
                "    run=V1Job(container=V1Container(\n"
                "        image='busybox:1.36',\n"
                "        command=['sh', '-c'],\n"
                "        args=['echo {{ epochs }}'],\n"
                "    )),\n"
                ")\n"
            )

            result = self.runner.invoke(
                run,
                [
                    "--project=owner/project",
                    "-pm",
                    "{}:component".format(source),
                    "-P",
                    "epochs=1",
                ],
            )

        assert result.exit_code == 0, (result.output, result.exception)
        create_run.assert_called_once()
        submitted = json.loads(create_run.call_args.kwargs["body"].content)
        assert submitted["version"] == 1.1
        assert submitted["kind"] == "operation"
        assert submitted["params"] == {"epochs": {"value": "1"}}
        assert submitted["component"]["kind"] == "component"
        assert submitted["component"]["version"] == 1.1
        assert submitted["component"]["run"]["container"]["image"] == "busybox:1.36"

    @patch("polyaxon._utils.cache.cache")
    @patch("polyaxon._cli.dashboard.get_dashboard_url", return_value="run-url")
    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._sdk.api.runs_v1_api.RunsV1Api.create_run")
    def test_run_shared_file_submits_native_content(
        self, create_run, resolve_project, dashboard, cache
    ):
        resolve_project.return_value = ("owner", None, "project")
        create_run.return_value = V1Run(
            uuid="8aac02e3a62a4f0aaa257c59da5eab80",
            name="shared",
            settings=V1RunSettings(),
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "job.yml"
            for kind in (None, "operation"):
                with self.subTest(kind=kind):
                    create_run.reset_mock()
                    content = {
                        "inputs": [{"name": "count", "type": "int"}],
                        "params": {"count": 3},
                        "presets": ["team-defaults"],
                        "run": {
                            "kind": "job",
                            "container": {
                                "image": "busybox:1.36",
                                "command": ["sh", "-c"],
                                "args": ['echo "{{ count }} {{ message }}"'],
                                "resources": {"limits": {"nvidia.com/gpu": 1}},
                            },
                        },
                    }
                    if kind:
                        content["kind"] = kind
                    source.write_text(json.dumps(content))

                    result = self.runner.invoke(
                        run,
                        [
                            "--project=owner/project",
                            "-f",
                            str(source),
                            "-P",
                            "message=from-cli",
                        ],
                    )

                    assert result.exit_code == 0, (result.output, result.exception)
                    create_run.assert_called_once()
                    body = create_run.call_args.kwargs["body"]
                    assert isinstance(body.content, str)
                    submitted = json.loads(body.content)
                    assert "component" not in submitted
                    assert submitted["run"] == content["run"]
                    assert submitted["inputs"] == content["inputs"]
                    assert submitted["params"] == {
                        "count": {"value": 3},
                        "message": {"value": "from-cli"},
                    }
                    assert submitted["presets"] == ["team-defaults"]

    @patch("polyaxon._utils.cache.cache")
    @patch("polyaxon._cli.dashboard.get_dashboard_url", return_value="run-url")
    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._sdk.api.runs_v1_api.RunsV1Api.create_run")
    def test_run_shared_reference_with_multiple_files(
        self, create_run, resolve_project, dashboard, cache
    ):
        resolve_project.return_value = ("owner", None, "project")
        create_run.return_value = V1Run(
            uuid="8aac02e3a62a4f0aaa257c59da5eab80",
            name="shared",
            settings=V1RunSettings(),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            templates = root / "templates"
            templates.mkdir()
            (templates / "job.yml").write_text(
                "inputs: [{name: count, type: int}]\n"
                "params: {count: 1}\n"
                "run:\n"
                "  kind: job\n"
                "  container:\n"
                "    image: busybox:1.36\n"
                "    resources: {limits: {nvidia.com/gpu: 1}}\n"
            )
            source = root / "run.yml"
            source.write_text(
                "pathRef: ./templates/job.yml\n"
                "params: {count: 2}\n"
                "run:\n"
                "  kind: job\n"
                "  container: {image: local:v1}\n"
            )
            first = root / "first.yml"
            first.write_text(
                "patchStrategy: post_merge\n"
                "params: {count: 5}\n"
                "run:\n"
                "  container: {image: first:v2}\n"
            )
            second = root / "second.yml"
            second.write_text(
                "patchStrategy: pre_merge\n"
                "params: {count: 7}\n"
                "run:\n"
                "  container: {image: second:v3}\n"
                "  environment:\n"
                "    annotations: {source: second}\n"
            )

            result = self.runner.invoke(
                run,
                [
                    "--project=owner/project",
                    "-f",
                    str(source),
                    "-f",
                    str(first),
                    "-f",
                    str(second),
                ],
            )

        assert result.exit_code == 0, (result.output, result.exception)
        create_run.assert_called_once()
        submitted = json.loads(create_run.call_args.kwargs["body"].content)
        assert submitted["pathRef"] == "./templates/job.yml"
        assert "component" not in submitted["component"]
        assert submitted["component"]["params"] == {"count": {"value": 1}}
        assert submitted["component"]["run"]["container"]["image"] == "busybox:1.36"
        assert submitted["params"] == {"count": {"value": 5}}
        assert submitted["run"]["container"]["image"] == "first:v2"
        assert submitted["run"]["environment"]["annotations"] == {"source": "second"}

        compiled = OperationSpecification.compile_operation(
            OperationSpecification.read(submitted)
        )
        assert compiled.run.container.image == "first:v2"
        assert compiled.run.container.resources == {"limits": {"nvidia.com/gpu": 1}}

    @patch("polyaxon._utils.cache.cache")
    @patch("polyaxon._cli.dashboard.get_dashboard_url", return_value="run-url")
    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._client.run.RunClient")
    def test_run_relative_path_ref_submits_resolved_component(
        self, run_client, resolve_project, dashboard, cache
    ):
        resolve_project.return_value = ("owner", None, "project")
        client = run_client.return_value
        client.create.return_value = SimpleNamespace(
            uuid="8aac02e3a62a4f0aaa257c59da5eab80",
            name="run",
            pending=None,
            settings=V1RunSettings(),
        )
        client.client.sanitize_for_serialization.return_value = {}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            templates = root / "templates"
            templates.mkdir()
            (templates / "job.yml").write_text(
                "kind: component\n"
                "inputs:\n"
                "  - name: message\n"
                "    type: str\n"
                "    isOptional: true\n"
                "run:\n"
                "  kind: job\n"
                "  container: {image: busybox:1.36}\n"
            )
            source = root / "run.yml"
            source.write_text(
                "kind: operation\n"
                "pathRef: ./templates/job.yml\n"
                "runPatch:\n"
                "  container: {image: patched:v2}\n"
            )

            result = self.runner.invoke(
                run,
                [
                    "--project=owner/project",
                    "-f",
                    str(source),
                    "-P",
                    "message=from-cli",
                ],
            )

        assert result.exit_code == 0, (result.output, result.exception)
        client.create.assert_called_once()
        submitted = client.create.call_args.kwargs["content"]
        assert submitted.path_ref == "./templates/job.yml"
        assert submitted.component.run.container.image == "busybox:1.36"
        assert submitted.params["message"].value == "from-cli"
        assert submitted.run_patch["container"]["image"] == "patched:v2"

        stored = OperationSpecification.read(submitted.to_dict())
        compiled = OperationSpecification.compile_operation(stored)
        assert compiled.run.container.image == "patched:v2"

    @patch("polyaxon._utils.cache.cache")
    @patch("polyaxon._cli.dashboard.get_dashboard_url", return_value="run-url")
    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._client.run.RunClient")
    def test_run_multiple_files_preserves_legacy_patch_order(
        self, run_client, resolve_project, dashboard, cache
    ):
        resolve_project.return_value = ("owner", None, "project")
        client = run_client.return_value
        client.create.return_value = SimpleNamespace(
            uuid="8aac02e3a62a4f0aaa257c59da5eab80",
            name="run",
            pending=None,
            settings=V1RunSettings(),
        )
        client.client.sanitize_for_serialization.return_value = {}

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "base.yml"
            base.write_text(
                "kind: operation\n"
                "component:\n"
                "  run:\n"
                "    kind: job\n"
                "    container: {image: base:v1}\n"
                "runPatch:\n"
                "  container: {image: initial:v1}\n"
            )
            first = Path(directory) / "first.yml"
            first.write_text(
                "kind: operation\n"
                "patchStrategy: post_merge\n"
                "runPatch:\n"
                "  container: {image: first:v2}\n"
            )
            second = Path(directory) / "second.yml"
            second.write_text(
                "kind: operation\n"
                "patchStrategy: pre_merge\n"
                "runPatch:\n"
                "  container: {image: second:v3}\n"
                "  environment:\n"
                "    annotations: {source: second}\n"
            )

            result = self.runner.invoke(
                run,
                [
                    "--project=owner/project",
                    "-f",
                    str(base),
                    "-f",
                    str(first),
                    "-f",
                    str(second),
                ],
            )

        assert result.exit_code == 0, (result.output, result.exception)
        client.create.assert_called_once()
        submitted = client.create.call_args.kwargs["content"]
        assert submitted.component.run.container.image == "base:v1"
        assert submitted.run_patch["container"]["image"] == "first:v2"
        assert submitted.run_patch["environment"]["annotations"] == {"source": "second"}

        stored = OperationSpecification.read(submitted.to_dict())
        compiled = OperationSpecification.compile_operation(stored)
        assert compiled.run.container.image == "first:v2"
        assert compiled.run.environment.annotations == {"source": "second"}

    @patch("polyaxon._utils.cache.cache")
    @patch("polyaxon._cli.dashboard.get_dashboard_url", return_value="run-url")
    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._client.run.RunClient")
    def test_run_component_file_submits_wrapped_operation(
        self, run_client, resolve_project, dashboard, cache
    ):
        resolve_project.return_value = ("owner", None, "project")
        client = run_client.return_value
        client.create.return_value = SimpleNamespace(
            uuid="8aac02e3a62a4f0aaa257c59da5eab80",
            name="run",
            pending=None,
            settings=V1RunSettings(),
        )
        client.client.sanitize_for_serialization.return_value = {}

        result = self.runner.invoke(
            run,
            [
                "--project=owner/project",
                "--file=tests/fixtures/plain/simple_job.yml",
            ],
        )

        assert result.exit_code == 0, (result.output, result.exception)
        client.create.assert_called_once()
        submitted = client.create.call_args.kwargs["content"]
        assert submitted.kind == "operation"
        assert submitted.component.kind == "component"
        assert submitted.component.run.container.image == "python-with-boto3"
        assert submitted.component.run.container.command == "python download-s3-bucket"

        stored = OperationSpecification.read(submitted.to_dict())
        compiled = OperationSpecification.compile_operation(stored)
        assert compiled.run.container.image == "python-with-boto3"
        assert compiled.run.container.command == "python download-s3-bucket"
        assert compiled.run.container.resources == {
            "requests": {"nvidia.com/gpu": 1},
            "limits": {"nvidia.com/gpu": 1},
        }
        assert compiled.run.to_dict()["volumes"][0] == {
            "name": "foo",
            "secret": {"secretName": "mysecret"},
        }

    @patch("polyaxon._cli.run._run")
    @patch("polyaxon._cli.context.resolve_project")
    def test_run_strict_params(self, resolve_project, run_operation):
        resolve_project.return_value = ("owner", None, "project")
        cases = (
            ([], None),
            (["--strict-params"], True),
            (["--no-strict-params"], False),
        )
        for options, strict_params in cases:
            with self.subTest(strict_params=strict_params):
                run_operation.reset_mock()
                result = self.runner.invoke(
                    run,
                    [
                        "--project=owner/project",
                        "--file=tests/fixtures/plain/simple_job.yml",
                        "-P",
                        "extra=1",
                        *options,
                    ],
                )
                if strict_params:
                    assert result.exit_code == 1, result.output
                    assert "undeclared param" in result.output
                    run_operation.assert_not_called()
                else:
                    assert result.exit_code == 0, (result.output, result.exception)
                    run_operation.assert_called_once()
                    op_spec = run_operation.call_args.kwargs["op_spec"]
                    assert op_spec.strict_params is strict_params
                    assert op_spec.params["extra"].value == "1"

    @patch("polyaxon._cli.run._run")
    @patch("polyaxon._cli.context.resolve_project")
    def test_run_without_cache_option(self, resolve_project, run_operation):
        resolve_project.return_value = ("owner", None, "project")

        result = self.runner.invoke(
            run,
            [
                "--project=owner/project",
                "--file={}".format(
                    os.path.abspath("tests/fixtures/plain/simple_job.yml")
                ),
            ],
        )

        assert result.exit_code == 0, result.output
        assert run_operation.call_count == 1
        assert run_operation.call_args.kwargs["symlink_mode"] == "skip"
        assert run_operation.call_args.kwargs["symlink_report_limit"] == 20

    @patch("polyaxon._cli.run._run")
    @patch("polyaxon._cli.context.resolve_project")
    def test_run_symlink_options(self, resolve_project, run_operation):
        resolve_project.return_value = ("owner", None, "project")
        for mode in SYMLINK_MODES:
            with self.subTest(mode=mode):
                result = self.runner.invoke(
                    run,
                    [
                        "--project=owner/project",
                        "--file=tests/fixtures/plain/simple_job.yml",
                        "--upload",
                        "--symlink-mode",
                        mode,
                        "--symlink-report-limit",
                        "2",
                    ],
                )
                assert result.exit_code == 0, (result.output, result.exception)
                assert run_operation.call_args.kwargs["symlink_mode"] == mode
                assert run_operation.call_args.kwargs["symlink_report_limit"] == 2

    @patch("polyaxon._cli.run._run")
    def test_run_invalid_symlink_options(self, run_operation):
        for options in (
            ["--symlink-mode", "preserve"],
            ["--symlink-report-limit", "-1"],
        ):
            result = self.runner.invoke(run, options)
            assert result.exit_code == 2, result.output
        run_operation.assert_not_called()

    @patch("polyaxon._cli.operations.approve")
    @patch("polyaxon._polyaxonfile.CompiledOperationSpecification.read")
    @patch("polyaxon._utils.cache.cache")
    @patch("polyaxon._cli.dashboard.get_dashboard_url", return_value="run-url")
    @patch("polyaxon._cli.context.resolve_project")
    @patch("polyaxon._client.run.RunClient")
    def test_run_upload_and_mount_only_symlinks(
        self, run_client, resolve_project, dashboard, cache, read_spec, approve
    ):
        resolve_project.return_value = ("owner", None, "project")
        client = run_client.return_value
        client.create.return_value = SimpleNamespace(
            uuid="8aac02e3a62a4f0aaa257c59da5eab80",
            name="run",
            pending=V1RunPending.UPLOAD,
            settings=V1RunSettings(),
            content={},
        )
        client.client.sanitize_for_serialization.return_value = {}
        client._no_op = False
        client._is_offline = False
        client._manual_exceptions_handling = True

        def upload_directory(**kwargs):
            return RunClient.upload_artifacts_dir(client, **kwargs)

        client.upload_artifacts_dir.side_effect = upload_directory
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "content.txt"
            source.write_text("content")
            root = Path(directory) / "upload"
            root.mkdir()
            (root / "link").symlink_to(source)
            read_spec.return_value.get_resolved_mount.return_value = [
                SimpleNamespace(path_from=str(root), path_to="uploads")
            ]
            for upload_args in (
                ["--upload", "--upload-from", str(root)],
                ["--mount", str(root)],
            ):
                for mode in (None, "error"):
                    with self.subTest(upload=upload_args[0], mode=mode):
                        client.reset_mock()
                        approve.reset_mock()
                        args = [
                            "--project=owner/project",
                            "--file=tests/fixtures/plain/simple_job.yml",
                            *upload_args,
                            "--symlink-report-limit",
                            "2",
                        ]
                        if mode:
                            args += ["--symlink-mode", mode]
                        result = self.runner.invoke(run, args)
                        assert result.exit_code == 1, (
                            result.output,
                            result.exception,
                        )
                        assert client.create.call_args.kwargs["pending"] == (
                            V1RunPending.UPLOAD
                        )
                        client.log_failed.assert_called_once()
                        status = client.log_failed.call_args.kwargs
                        assert status["reason"] == (
                            "OperationCli" if mode else "UploadEmpty"
                        )
                        if not mode:
                            assert str(root) in status["message"]
                            assert "symlink mode `skip`" in status["message"]
                            assert "--symlink-mode resolve-safe" in status["message"]
                        approve.assert_not_called()
                        client.upload_artifacts.assert_not_called()
                        kwargs = client.upload_artifacts_dir.call_args.kwargs
                        assert kwargs["symlink_mode"] == (mode or "skip")
                        assert kwargs["symlink_report_limit"] == 2
