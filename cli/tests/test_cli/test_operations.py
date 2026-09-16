import csv
import inspect
from io import StringIO
import json
from mock import patch
from pathlib import Path
import pytest
from requests import Request, Response
import tempfile

import click
from click.testing import CliRunner
from rich.console import Console
from rich.theme import Theme

from clipped.formatting import Printer
from clipped.utils.json import orjson_loads
from polyaxon._cli.init import init
from polyaxon._cli.operations import ops, upload
from polyaxon._client.run import UPLOAD_SKIPPED
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._managers.run import RunConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon._sdk.schemas.v1_list_runs_response import V1ListRunsResponse
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._sdk.schemas.v1_run import V1Run
from polyaxon._sdk.schemas.v1_user import V1User
from polyaxon._utils.cli_constants import SYMLINK_MODES
from polyaxon.exceptions import PolyaxonClientException
from tests.test_cli.utils import BaseCommandTestCase


RUN_UUID = "8aac02e3a62a4f0aaa257c59da5eab80"
LIST_RUN_UUIDS = (RUN_UUID, "85f07474-715c-4f04-b801-dbd0466d749e")
K8S_EXIT_7 = (
    '{"status":"Failure","details":{"causes":[{"reason":"ExitCode","message":"7"}]}}'
)


@pytest.mark.cli_mark
class TestCliUploads(BaseCommandTestCase):
    @patch("polyaxon._client.run.RunClient")
    def test_upload_symlink_options(self, run_client):
        run_client.return_value.upload_artifacts_dir.return_value.status_code = 200
        for mode in (None, *SYMLINK_MODES):
            with self.subTest(mode=mode):
                args = ["upload", "-p", "owner/project", "-uid", RUN_UUID]
                if mode:
                    args += ["--symlink-mode", mode, "--symlink-report-limit", "2"]
                result = self.runner.invoke(ops, args)

                assert result.exit_code == 0, (result.output, result.exception)
                kwargs = run_client.return_value.upload_artifacts_dir.call_args.kwargs
                assert kwargs["symlink_mode"] == (mode or "skip")
                assert kwargs["symlink_report_limit"] == (2 if mode else 20)
                run_client.return_value.upload_artifact.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    def test_upload_symlink_invalid_options(self, run_client):
        for options in (
            ["--symlink-mode", "unknown"],
            ["--symlink-mode", "preserve"],
            ["--symlink-report-limit", "-1"],
        ):
            result = self.runner.invoke(ops, ["upload", *options])
            assert result.exit_code == 2, result.output
            run_client.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    def test_upload_symlink_preflight_error(self, run_client):
        run_client.return_value.upload_artifacts_dir.side_effect = (
            PolyaxonClientException(
                "link -> ../outside: link target is outside the upload root. "
                "Use --symlink-mode skip to omit it."
            )
        )
        result = self.runner.invoke(
            ops, ["upload", "-p", "owner/project", "-uid", RUN_UUID]
        )
        assert result.exit_code == 1, result.output
        output = " ".join(result.output.split())
        assert "link -> ../outside" in output
        assert "--symlink-mode skip" in output

    @patch("polyaxon._client.run.RunClient")
    def test_upload_explicit_file_symlink_keeps_single_file_behavior(self, run_client):
        run_client.return_value.upload_artifact.return_value.status_code = 200
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "content.txt"
            source.write_text("content")
            link = Path(directory) / "link"
            link.symlink_to(source)
            result = self.runner.invoke(
                ops,
                [
                    "upload",
                    "-p",
                    "owner/project",
                    "-uid",
                    RUN_UUID,
                    "--path-from",
                    str(link),
                    "--symlink-mode",
                    "error",
                ],
            )
            assert result.exit_code == 0, (result.output, result.exception)
            assert run_client.return_value.upload_artifact.call_args.kwargs[
                "filepath"
            ] == str(link)
            run_client.return_value.upload_artifacts_dir.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    def test_upload_symlink_defaults_for_indirect_invocation(self, run_client):
        run_client.return_value.upload_artifacts_dir.return_value.status_code = 200

        @click.command()
        @click.pass_context
        def upload_code(ctx):
            ctx.invoke(upload, project="owner/project", uid=RUN_UUID)

        result = self.runner.invoke(upload_code, obj={})
        assert result.exit_code == 0, (result.output, result.exception)
        kwargs = run_client.return_value.upload_artifacts_dir.call_args.kwargs
        assert kwargs["symlink_mode"] == "skip"
        assert kwargs["symlink_report_limit"] == 20

    @patch("polyaxon._client.run.RunClient")
    def test_upload_status_failure_does_not_hide_preflight_error(self, run_client):
        run_client.return_value.upload_artifacts_dir.side_effect = (
            PolyaxonClientException(
                "link target is outside the upload root; token=fake-token"
            )
        )
        run_client.return_value.log_failed.side_effect = PolyaxonClientException(
            "status update unavailable"
        )

        @click.command()
        @click.pass_context
        def upload_code(ctx):
            ctx.invoke(upload, project="owner/project", uid=RUN_UUID, sync_failure=True)

        result = self.runner.invoke(upload_code, obj={})
        assert result.exit_code == 1, result.output
        output = " ".join(result.output.split())
        assert "outside the upload root" in output
        assert "status update unavailable" in output
        assert "token=fake-token" in output
        run_client.return_value.log_failed.assert_called_once_with(
            reason="OperationCli",
            message="Operation failed uploading artifacts. "
            "Check CLI output for details.",
        )

    @patch("polyaxon._client.run.RunClient")
    def test_empty_selection_is_distinct_from_missing_upload_response(self, run_client):
        for sync_failure in (False, True):
            for response in (UPLOAD_SKIPPED, None):
                with self.subTest(sync_failure=sync_failure, response=response):
                    client = run_client.return_value
                    client.reset_mock()
                    client.upload_artifacts_dir.return_value = response
                    args = ["upload", "-p", "owner/project", "-uid", RUN_UUID]
                    if sync_failure:
                        args.append("--sync-failure")
                    result = self.runner.invoke(ops, args)
                    empty = response is UPLOAD_SKIPPED
                    assert result.exit_code == (0 if empty and not sync_failure else 1)
                    output = " ".join(result.output.split())
                    assert "Artifacts uploaded" not in output
                    if sync_failure:
                        client.log_failed.assert_called_once()
                        status = client.log_failed.call_args.kwargs
                        assert status["reason"] == (
                            "UploadEmpty" if empty else "OperationCli"
                        )
                        assert status["message"] in output
                    else:
                        client.log_failed.assert_not_called()
                        if empty:
                            assert "upload skipped" in output
                    if empty:
                        assert "Upload is empty" in output
                        assert "folder contains files" in output
                        assert "ignore rules" in output
                        assert "symlinks" in output
                        assert "--symlink-mode resolve-safe" in output
                        assert "--symlink-mode resolve-all" in output
                    else:
                        assert "No upload response was received" in output

    @patch("polyaxon._client.run.RunClient")
    def test_empty_upload_status_failure_preserves_details(self, run_client):
        client = run_client.return_value
        client.upload_artifacts_dir.return_value = UPLOAD_SKIPPED
        client.log_failed.side_effect = PolyaxonClientException(
            "status update unavailable"
        )
        result = self.runner.invoke(
            ops,
            ["upload", "-p", "owner/project", "-uid", RUN_UUID, "--sync-failure"],
        )
        assert result.exit_code == 1, result.output
        output = " ".join(result.output.split())
        assert "status update unavailable" in output
        assert "Upload is empty" in output
        assert "--symlink-mode resolve-safe" in output

    @patch("polyaxon._client.run.RunClient")
    def test_upload_failed_response_includes_body_without_request_headers(
        self, run_client
    ):
        client = run_client.return_value
        response = Response()
        response.status_code = 500
        response._content = b"Upload unavailable"
        response.request = Request(
            "POST",
            "https://example.test/upload",
            headers={"Authorization": "Bearer fake-token"},
        ).prepare()
        client.upload_artifacts_dir.return_value = response
        result = self.runner.invoke(
            ops,
            ["upload", "-p", "owner/project", "-uid", RUN_UUID, "--sync-failure"],
        )
        assert result.exit_code == 1, result.output
        client.log_failed.assert_called_once_with(
            reason="OperationCli",
            message="Error uploading artifacts. Status: 500. "
            "Error: b'Upload unavailable'.",
        )
        output = " ".join(result.output.split())
        assert "Status: 500" in output
        assert "Upload unavailable" in output
        assert "fake-token" not in client.log_failed.call_args.kwargs["message"]


@pytest.mark.cli_mark
class TestCliCachedRunContext(BaseCommandTestCase):
    def setUp(self):
        super().setUp()
        if "mix_stderr" in inspect.signature(CliRunner.__init__).parameters:
            self.runner = CliRunner(mix_stderr=False)
        console_width = pytest.MonkeyPatch()
        console_width.setattr(Printer.stderr_console, "width", 200)
        self.addCleanup(console_width.undo)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        # Cache paths must be printed literally, even with Rich markup characters.
        self.local_cache = Path(directory.name) / "local[red]" / ".polyaxon"
        self.global_cache = Path(directory.name) / "global" / ".polyaxon"
        for manager in (
            ProjectConfigManager,
            RunConfigManager,
            UserConfigManager,
        ):
            patcher = patch.multiple(
                manager,
                CONFIG_PATH=None,
                _PROJECT=str(self.local_cache),
                _PROJECT_PATH=str(self.global_cache),
            )
            patcher.start()
            self.addCleanup(patcher.stop)
        ProjectConfigManager.set_config(
            V1Project(owner="owner", name="project-a"), visibility="local"
        )
        RunConfigManager.set_config(
            V1Run(uuid=RUN_UUID, owner="owner", project="project-a"),
            visibility="local",
        )

    def invoke_ops(self, args, show_context=True):
        return self.runner.invoke(ops, args, obj={"show_context": show_context})

    @patch("polyaxon.cli.configure_logger")
    @patch("polyaxon.settings.set_cli_config")
    @patch("polyaxon._client.run.RunClient")
    def test_global_context_flags_default_to_quiet(
        self, run_client, set_cli_config, configure_logger
    ):
        from polyaxon import settings
        from polyaxon._schemas.cli import CliConfig
        from polyaxon.cli import cli

        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "results": []
        }
        with patch.object(settings, "CLI_CONFIG", CliConfig()):
            for args, expect_context in (
                ([], False),
                (["--show-context"], True),
                (["--verbose"], True),
            ):
                with self.subTest(args=args):
                    result = self.runner.invoke(
                        cli, args + ["ops", "ls", "--output", "json"]
                    )

                    assert result.exit_code == 0, result.output
                    assert orjson_loads(result.stdout) == {"results": []}
                    if expect_context:
                        assert self.context_rows(result)["Project"][0] == "project-a"
                    else:
                        assert result.stderr == ""

    @patch("polyaxon._client.run.RunClient")
    def test_hidden_context_still_rejects_cached_run_conflicts(self, run_client):
        result = self.invoke_ops(
            ["statuses", "--project", "owner/project-b"], show_context=False
        )

        self.assert_conflicting_context(result, self.local_cache / ".run")
        assert "owner: explicit; project: explicit" in result.stderr
        run_client.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    def test_conflicts_report_project_sources_with_or_without_context(self, run_client):
        for visibility in ("local", "global"):
            if visibility == "global":
                (self.local_cache / ".project").unlink()
            ProjectConfigManager.set_config(
                V1Project(owner="owner", name="project-b"), visibility=visibility
            )
            project_path = ProjectConfigManager.get_config_filepath(create=False)
            for show_context in (False, True):
                with self.subTest(visibility=visibility, show_context=show_context):
                    result = self.invoke_ops(["statuses"], show_context=show_context)

                    self.assert_conflicting_context(result, self.local_cache / ".run")
                    assert (
                        f"owner: {visibility} cache · {project_path}" in result.stderr
                    )
                    assert (
                        f"project: {visibility} cache · {project_path}" in result.stderr
                    )
                    run_client.assert_not_called()

    def assert_conflicting_context(self, result, run_path):
        assert result.exit_code != 0
        assert "owner/project-a" in result.stderr
        assert "owner/project-b" in result.stderr
        assert RUN_UUID in result.stderr
        assert str(run_path) in result.stderr
        assert "Context:" not in result.stderr

    def context_rows(self, result):
        assert result.stderr.count("Context:") == 1
        assert "\x1b[" not in result.stderr
        rows = [
            line.split(None, 2)
            for line in result.stderr.splitlines()
            if line.lstrip().startswith(("Owner ", "Project ", "Run "))
        ]
        fields = {name: (value, source.rstrip()) for name, value, source in rows}
        assert len(fields) == len(rows)
        return fields

    @patch("polyaxon._client.run.RunClient")
    def test_statuses_rejects_explicit_project_conflict(self, run_client):
        result = self.invoke_ops(["--project", "owner/project-b", "statuses"])

        self.assert_conflicting_context(result, self.local_cache / ".run")
        run_client.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    def test_stop_rejects_explicit_project_conflict(self, run_client):
        result = self.invoke_ops(["--project", "owner/project-b", "stop", "--yes"])

        self.assert_conflicting_context(result, self.local_cache / ".run")
        run_client.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    @patch("polyaxon._client.project.ProjectClient")
    def test_statuses_rejects_stale_run_after_project_reinit(
        self, project_client, run_client
    ):
        project_client.return_value.client.sanitize_for_serialization.return_value = {
            "owner": "owner",
            "name": "project-b",
        }

        initialized = self.runner.invoke(
            init, ["--project", "owner/project-b", "--yes"]
        )

        assert initialized.exit_code == 0, initialized.output
        assert ProjectConfigManager.get_config().name == "project-b"
        assert RunConfigManager.get_config().uuid == RUN_UUID
        assert RunConfigManager.get_config().project == "project-a"

        result = self.invoke_ops(["statuses"])

        self.assert_conflicting_context(result, self.local_cache / ".run")
        run_client.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    def test_list_reports_local_project_cache_on_stderr(self, run_client):
        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "results": []
        }

        result = self.invoke_ops(["ls", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert orjson_loads(result.stdout) == {"results": []}
        source = f"local cache · {self.local_cache / '.project'}"
        assert self.context_rows(result) == {
            "Owner": ("owner", source),
            "Project": ("project-a", source),
        }
        assert RUN_UUID not in result.stderr

    @patch("polyaxon._client.run.RunClient")
    def test_list_reports_global_project_cache_on_stderr(self, run_client):
        ProjectConfigManager.purge(visibility="local")
        ProjectConfigManager.set_config(
            V1Project(owner="owner", name="project-b"), visibility="global"
        )
        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "results": []
        }

        result = self.invoke_ops(["ls", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert orjson_loads(result.stdout) == {"results": []}
        source = f"global cache · {self.global_cache / '.project'}"
        assert self.context_rows(result) == {
            "Owner": ("owner", source),
            "Project": ("project-b", source),
        }
        assert str(self.local_cache) not in result.stderr
        assert RUN_UUID not in result.stderr

    @patch("polyaxon._client.run.RunClient")
    def test_list_reports_owner_from_user_cache(self, run_client):
        UserConfigManager.set_config(V1User(organization="cached-owner"))
        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "results": []
        }

        result = self.invoke_ops(["ls", "--project", "project-a", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert orjson_loads(result.stdout) == {"results": []}
        assert self.context_rows(result) == {
            "Owner": (
                "cached-owner",
                f"global cache · {self.global_cache / '.user'}",
            ),
            "Project": ("project-a", "explicit"),
        }
        run_client.assert_called_once_with(
            owner="cached-owner", project="project-a", manual_exceptions_handling=True
        )

    @patch("polyaxon._client.run.RunClient")
    def test_list_keeps_project_and_fallback_owner_sources_separate(self, run_client):
        ProjectConfigManager.set_config(V1Project(name="project-a"), visibility="local")
        UserConfigManager.set_config(V1User(organization="cached-owner"))
        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "results": []
        }

        result = self.invoke_ops(["ls", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert orjson_loads(result.stdout) == {"results": []}
        assert self.context_rows(result) == {
            "Owner": (
                "cached-owner",
                f"global cache · {self.global_cache / '.user'}",
            ),
            "Project": (
                "project-a",
                f"local cache · {self.local_cache / '.project'}",
            ),
        }

    @patch("polyaxon._client.run.RunClient")
    def test_list_with_explicit_project_does_not_report_cache(self, run_client):
        UserConfigManager.set_config(V1User(organization="cached-owner"))
        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "results": []
        }

        result = self.invoke_ops(
            ["ls", "--project", "owner/project-b", "--output", "json"]
        )

        assert result.exit_code == 0, result.output
        assert orjson_loads(result.stdout) == {"results": []}
        assert result.stderr == ""

    @patch("polyaxon._client.run.RunClient")
    def test_get_reports_local_run_cache_on_stderr(self, run_client):
        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "uuid": RUN_UUID
        }

        result = self.invoke_ops(["get", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert orjson_loads(result.stdout)["uuid"] == RUN_UUID
        source = f"local cache · {self.local_cache / '.project'}"
        assert self.context_rows(result) == {
            "Owner": ("owner", source),
            "Project": ("project-a", source),
            "Run": (RUN_UUID, f"local cache · {self.local_cache / '.run'}"),
        }
        assert "Cached owner/project metadata is incomplete;" not in " ".join(
            result.stderr.split()
        )
        run_client.assert_called_once_with(
            owner="owner",
            project="project-a",
            run_uuid=RUN_UUID,
            manual_exceptions_handling=True,
        )

    @patch("polyaxon._env_vars.getters.run.logger")
    @patch("polyaxon._client.mixin.PolyaxonClient")
    def test_cli_resolved_run_is_not_reported_again_by_client(
        self, client_class, logger
    ):
        sdk = client_class.return_value
        sdk.is_async = False
        sdk.config = None
        sdk.runs_v1.get_run.return_value = V1Run(
            uuid=RUN_UUID, owner="owner", project="project-a"
        )
        sdk.sanitize_for_serialization.return_value = {"uuid": RUN_UUID}

        result = self.invoke_ops(["get", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert orjson_loads(result.stdout)["uuid"] == RUN_UUID
        assert self.context_rows(result)["Run"][0] == RUN_UUID
        assert result.stderr.count(RUN_UUID) == 1
        logger.info.assert_not_called()
        logger.warning.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    def test_get_reports_global_run_cache_on_stderr(self, run_client):
        RunConfigManager.purge(visibility="local")
        RunConfigManager.set_config(
            V1Run(uuid=RUN_UUID, owner="owner", project="project-a"),
            visibility="global",
        )
        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "uuid": RUN_UUID
        }

        result = self.invoke_ops(["get", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert orjson_loads(result.stdout)["uuid"] == RUN_UUID
        fields = self.context_rows(result)
        assert fields["Run"] == (
            RUN_UUID,
            f"global cache · {self.global_cache / '.run'}",
        )
        assert fields["Project"] == (
            "project-a",
            f"local cache · {self.local_cache / '.project'}",
        )
        assert str(self.local_cache / ".run") not in result.stderr
        assert "Cached owner/project metadata is incomplete;" not in " ".join(
            result.stderr.split()
        )

    @patch("polyaxon._client.run.RunClient")
    def test_get_warns_for_incomplete_cached_ownership(self, run_client):
        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "uuid": RUN_UUID
        }
        for owner, project in ((None, None), ("owner", None), (None, "project-a")):
            with self.subTest(owner=owner, project=project):
                RunConfigManager.set_config(
                    V1Run(uuid=RUN_UUID, owner=owner, project=project),
                    visibility="local",
                )

                result = self.invoke_ops(["get", "--output", "json"])

                assert result.exit_code == 0, result.output
                assert orjson_loads(result.stdout)["uuid"] == RUN_UUID
                fields = self.context_rows(result)
                assert fields["Project"] == (
                    "project-a",
                    f"local cache · {self.local_cache / '.project'}",
                )
                assert fields["Run"] == (
                    RUN_UUID,
                    f"local cache · {self.local_cache / '.run'}",
                )
                assert "Cached owner/project metadata is incomplete;" in " ".join(
                    result.stderr.split()
                )

    @patch("polyaxon._client.run.RunClient")
    def test_explicit_uuid_does_not_report_run_cache(self, run_client):
        explicit_uuid = "22222222222222222222222222222222"
        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "uuid": explicit_uuid
        }
        for owner, project in ((None, None), ("other-owner", "project-b")):
            with self.subTest(owner=owner, project=project):
                RunConfigManager.set_config(
                    V1Run(uuid=RUN_UUID, owner=owner, project=project),
                    visibility="local",
                )

                result = self.invoke_ops(
                    [
                        "get",
                        "--project",
                        "owner/project-a",
                        "--uid",
                        explicit_uuid,
                        "--output",
                        "json",
                    ],
                )

                assert result.exit_code == 0, result.output
                assert orjson_loads(result.stdout)["uuid"] == explicit_uuid
                assert result.stderr == ""
                run_client.assert_called_with(
                    owner="owner",
                    project="project-a",
                    run_uuid=explicit_uuid,
                    manual_exceptions_handling=True,
                )

    @patch("polyaxon._client.run.RunClient")
    def test_explicit_uuid_is_shown_alongside_cached_project(self, run_client):
        explicit_uuid = "22222222222222222222222222222222"
        run_client.return_value.client.sanitize_for_serialization.return_value = {
            "uuid": explicit_uuid
        }

        result = self.invoke_ops(["get", "--uid", explicit_uuid, "--output", "json"])

        assert result.exit_code == 0, result.output
        assert orjson_loads(result.stdout)["uuid"] == explicit_uuid
        source = f"local cache · {self.local_cache / '.project'}"
        assert self.context_rows(result) == {
            "Owner": ("owner", source),
            "Project": ("project-a", source),
            "Run": (explicit_uuid, "explicit"),
        }
        assert str(self.local_cache / ".run") not in result.stderr

    @patch("polyaxon._client.run.RunClient")
    def test_incomplete_cache_still_rejects_known_conflicts_before_notice(
        self, run_client
    ):
        for owner, project in (("other-owner", None), (None, "project-b")):
            with self.subTest(owner=owner, project=project):
                RunConfigManager.set_config(
                    V1Run(uuid=RUN_UUID, owner=owner, project=project),
                    visibility="local",
                )

                result = self.invoke_ops(["get", "--output", "json"])

                assert result.exit_code != 0
                assert result.stdout == ""
                assert "conflicts with project `owner/project-a`" in result.stderr
                assert "Context:" not in result.stderr
                run_client.assert_not_called()

    @patch("polyaxon._cli.operations.wait_for_running_condition")
    @patch("polyaxon._client.run.RunClient")
    def test_exec_keeps_cache_notices_off_streamed_stdout(self, run_client, wait):
        shell = ExecShell(stdout="out\n", stderr="err\n", error=K8S_EXIT_7)
        run_client.return_value.shell.return_value = shell

        result = self.invoke_ops(
            ["exec", "--pod", "pod-1", "--container", "main", "--", "echo", "hi"]
        )

        assert result.exit_code == 7, result.output
        assert result.stdout == "out\n"
        fields = self.context_rows(result)
        assert fields["Project"] == (
            "project-a",
            f"local cache · {self.local_cache / '.project'}",
        )
        assert fields["Run"] == (
            RUN_UUID,
            f"local cache · {self.local_cache / '.run'}",
        )
        assert result.stderr.endswith("err\n")
        assert shell.closed


class ExecShell:
    def __init__(self, stdout="", stderr="", error='{"status":"Success"}'):
        self.stdout = stdout
        self.stderr = stderr
        self.error = error
        self.open = True
        self.closed = False

    def is_open(self):
        return self.open

    def update(self, timeout=0):
        self.open = False

    def peek_stdout(self):
        return bool(self.stdout)

    def read_stdout(self):
        data = self.stdout
        self.stdout = ""
        return data

    def peek_stderr(self):
        return bool(self.stderr)

    def read_stderr(self):
        data = self.stderr
        self.stderr = ""
        return data

    def peek_channel(self, channel):
        return bool(self.error)

    def read_channel(self, channel):
        data = self.error
        self.error = ""
        return data

    def close(self):
        self.closed = True


@pytest.mark.cli_mark
class TestCliRuns(BaseCommandTestCase):
    @staticmethod
    def list_runs_response():
        return V1ListRunsResponse.model_construct(
            count=len(LIST_RUN_UUIDS),
            results=[
                V1Run.model_construct(
                    uuid=uuid,
                    name="long-operation-name-" * 20,
                    status="succeeded",
                    inputs={"parameter": "long-input-value-" * 20},
                    outputs={"result": "long-output-value-" * 20},
                )
                for uuid in LIST_RUN_UUIDS
            ],
        )

    def invoke_list_runs(self, options=(), width=80):
        output = StringIO()
        console = Console(
            file=output,
            width=width,
            color_system=None,
            theme=Theme(
                {
                    "header": "yellow",
                    "success": "green",
                    "info": "cyan",
                    "warning": "magenta",
                    "error": "red",
                    "white": "white",
                }
            ),
        )
        with patch.object(Printer, "console", console):
            result = self.runner.invoke(ops, ["ls", "-p", "admin/foo", *options])
        assert result.exit_code == 0, (
            result.output,
            output.getvalue(),
            result.exception,
        )
        return result, output.getvalue()

    @patch("polyaxon.client.RunClient.list")
    def test_list_runs(self, list_runs):
        list_runs.return_value = self.list_runs_response()
        cases = (
            ([], 20),
            (["--io"], 80),
            (["--columns", "name,uuid,status"], 80),
            (["--io", "--columns", "uuid,parameter,result"], 160),
        )

        for options, width in cases:
            with self.subTest(options=options, width=width):
                _, output = self.invoke_list_runs(options, width=width)

                for uuid in LIST_RUN_UUIDS:
                    assert uuid in output
                if "--io" in options:
                    assert "in.parameter" in output
                    assert "out.result" in output
                else:
                    assert "in.parameter" not in output
                    assert "out.result" not in output
                list_runs.assert_called_with(
                    limit=None, offset=None, query=None, sort=None
                )

        assert list_runs.call_count == len(cases)

    @patch("polyaxon.client.RunClient.list")
    def test_list_runs_omits_unselected_uuid(self, list_runs):
        list_runs.return_value = self.list_runs_response()

        _, output = self.invoke_list_runs(["--columns", "name,status"])

        assert "uuid" not in output
        for uuid in LIST_RUN_UUIDS:
            assert uuid not in output
        assert "name | status" in output

    @patch("polyaxon._client.run.RunClient")
    def test_list_runs_offline(self, run_client):
        runs = [V1Run(**run.to_dict()) for run in self.list_runs_response().results]
        with tempfile.TemporaryDirectory() as directory:
            for run in runs:
                run_path = Path(directory) / "runs" / run.uuid / "run.plx.json"
                run_path.parent.mkdir(parents=True)
                run_path.write_text(json.dumps(run.to_dict()), encoding="utf8")

            _, output = self.invoke_list_runs(
                ["--offline", "--path", directory, "--io"], width=20
            )

        for run in runs:
            assert run.uuid in output
        run_client.assert_not_called()

    @patch("polyaxon.client.RunClient.list")
    def test_list_runs_empty(self, list_runs):
        list_runs.return_value = V1ListRunsResponse(count=0, results=[])

        _, output = self.invoke_list_runs()

        assert "No runs found for project `admin/foo`." in output
        assert "Displayed columns" not in output
        assert "Runs:" not in output

    @patch("polyaxon.client.RunClient.list")
    def test_list_runs_json(self, list_runs):
        response = self.list_runs_response()
        list_runs.return_value = response

        result, table_output = self.invoke_list_runs(["--output", "json"], width=20)

        data = json.loads(result.output)
        assert [run["uuid"] for run in data["results"]] == list(LIST_RUN_UUIDS)
        assert data == response.to_dict()
        assert table_output == ""

    @patch("polyaxon.client.RunClient.list")
    def test_list_runs_csv(self, list_runs):
        list_runs.return_value = self.list_runs_response()

        for options in ([], ["--io"]):
            with self.subTest(options=options), self.runner.isolated_filesystem():
                self.invoke_list_runs(["--to-csv", *options], width=20)
                with Path("results.csv").open(encoding="utf8", newline="") as stream:
                    rows = list(csv.DictReader(stream))

                assert [row["uuid"] for row in rows] == list(LIST_RUN_UUIDS)
                assert [row["status"] for row in rows] == ["succeeded"] * 2
                if options:
                    assert rows[0]["in.parameter"] == "long-input-value-" * 20
                    assert rows[0]["out.result"] == "long-output-value-" * 20
                else:
                    assert "inputs" not in rows[0]
                    assert "outputs" not in rows[0]

    @patch("polyaxon.client.RunClient.refresh_data")
    @patch("polyaxon._managers.project.ProjectConfigManager.is_initialized")
    @patch("polyaxon._managers.project.ProjectConfigManager.get_config")
    @patch("polyaxon._managers.run.RunConfigManager.set_config")
    @patch("polyaxon._cli.operations.get_run_details")
    def test_get_run(
        self, get_run_details, set_config, get_config, is_initialized, get_run
    ):
        self.runner.invoke(
            ops,
            ["--project=admin/foo", "--uid=8aac02e3a62a4f0aaa257c59da5eab80", "get"],
        )
        assert get_run.call_count == 1
        assert set_config.call_count == 0
        assert is_initialized.call_count == 1
        assert get_config.call_count == 1
        assert get_run_details.call_count == 1

    @patch("polyaxon.client.RunClient.refresh_data")
    @patch("polyaxon._managers.project.ProjectConfigManager.is_initialized")
    @patch("polyaxon._utils.cache._is_same_project")
    @patch("polyaxon._managers.run.RunConfigManager.set_config")
    @patch("polyaxon._cli.operations.get_run_details")
    def test_get_run_cache(
        self, get_run_details, set_config, is_same_project, is_initialized, get_run
    ):
        is_initialized.return_value = True
        is_same_project.return_value = True
        self.runner.invoke(
            ops,
            ["--project=admin/foo", "--uid=8aac02e3a62a4f0aaa257c59da5eab80", "get"],
        )
        assert get_run.call_count == 1
        assert set_config.call_count == 1
        assert is_same_project.call_count == 1
        assert is_initialized.call_count == 1
        assert get_run_details.call_count == 1

    @patch("polyaxon.client.RunClient.update")
    def test_update_run(self, update_run):
        self.runner.invoke(ops, ["update"])
        assert update_run.call_count == 0

        self.runner.invoke(
            ops,
            [
                "--project=admin/foo",
                "--uid=8aac02e3a62a4f0aaa257c59da5eab80",
                "update",
                "--description=foo",
            ],
        )
        assert update_run.call_count == 1

    @patch("polyaxon.client.RunClient.stop")
    def test_stop_run(self, stop):
        self.runner.invoke(ops, ["stop"])
        assert stop.call_count == 0

        self.runner.invoke(
            ops,
            [
                "--project=admin/foo",
                "--uid=8aac02e3a62a4f0aaa257c59da5eab80",
                "stop",
                "-y",
            ],
        )
        assert stop.call_count == 1

    @patch("polyaxon.client.RunClient.restart")
    def test_restart_run(self, restart):
        self.runner.invoke(
            ops,
            [
                "--project=admin/foo",
                "--uid=8aac02e3a62a4f0aaa257c59da5eab80",
                "restart",
            ],
        )
        assert restart.call_count == 1

    @patch("polyaxon.client.RunClient.restart")
    def test_copy_run(self, copy):
        self.runner.invoke(ops, ["restart"])
        assert copy.call_count == 0

        self.runner.invoke(
            ops,
            [
                "--project=admin/foo",
                "--uid=8aac02e3a62a4f0aaa257c59da5eab80",
                "restart",
                "-c",
            ],
        )
        assert copy.call_count == 1

    @patch("polyaxon.client.RunClient.resume")
    def test_resume_run(self, resume):
        self.runner.invoke(
            ops,
            ["--project=admin/foo", "--uid=8aac02e3a62a4f0aaa257c59da5eab80", "resume"],
        )
        assert resume.call_count == 1

    @patch("polyaxon.client.RunClient.get_statuses")
    def test_run_statuses(self, get_statuses):
        self.runner.invoke(
            ops,
            [
                "--project=admin/foo",
                "--uid=8aac02e3a62a4f0aaa257c59da5eab80",
                "statuses",
            ],
        )
        assert get_statuses.call_count == 1

    @patch("polyaxon.client.RunClient.download_artifacts")
    def test_run_download_artifacts(self, download_outputs):
        self.runner.invoke(
            ops,
            [
                "--project=admin/foo",
                "--uid=8aac02e3a62a4f0aaa257c59da5eab80",
                "artifacts",
            ],
        )
        assert download_outputs.call_count == 1

    @patch("polyaxon._client.run.RunClient")
    def test_exec_requires_separator(self, run_client):
        result = self.runner.invoke(
            ops,
            ["exec", "-p", "admin/foo", "-uid", RUN_UUID, "ls", "-la"],
        )

        assert result.exit_code != 0
        assert "command required after --" in result.output
        run_client.assert_not_called()

    @patch("polyaxon._cli.operations.wait_for_running_condition")
    @patch("polyaxon._cli.context.resolve_run")
    @patch("polyaxon._client.run.RunClient")
    def test_exec_streams_output_and_exit_code(self, run_client, get_run, wait):
        get_run.return_value = ("admin", None, "foo", RUN_UUID)
        shell = ExecShell(stdout="out\n", stderr="err\n", error=K8S_EXIT_7)
        run_client.return_value.shell.return_value = shell

        result = self.runner.invoke(
            ops,
            [
                "exec",
                "-p",
                "admin/foo",
                "-uid",
                RUN_UUID,
                "--pod",
                "pod-1",
                "--container",
                "main",
                "--",
                "sh",
                "-lc",
                "echo hi",
            ],
        )

        assert result.exit_code == 7
        assert "out" in result.output
        assert "err" in result.output
        run_client.return_value.shell.assert_called_once_with(
            command=("sh", "-lc", "echo hi"),
            pod="pod-1",
            container="main",
            stdin=False,
            stdout=True,
            stderr=True,
            tty=False,
        )
        wait.assert_called_once_with(run_client.return_value)
        assert shell.closed

    @patch("polyaxon._cli.operations.wait_for_running_condition")
    @patch("polyaxon._cli.context.resolve_run")
    @patch("polyaxon._client.run.RunClient")
    def test_exec_returns_zero_on_success_status(self, run_client, get_run, wait):
        get_run.return_value = ("admin", None, "foo", RUN_UUID)
        run_client.return_value.shell.return_value = ExecShell(stdout="ok\n")

        result = self.runner.invoke(
            ops,
            ["exec", "-p", "admin/foo", "-uid", RUN_UUID, "--", "python", "-V"],
        )

        assert result.exit_code == 0
        assert "ok" in result.output
        run_client.return_value.shell.assert_called_once_with(
            command=("python", "-V"),
            pod=None,
            container=None,
            stdin=False,
            stdout=True,
            stderr=True,
            tty=False,
        )
