from mock import patch
import os
from pathlib import Path
import pytest
import tempfile
from types import SimpleNamespace

from polyaxon._cli.run import run
from polyaxon._client.run import RunClient
from polyaxon._flow.run.enums import V1RunPending
from polyaxon._sdk.schemas.v1_run_settings import V1RunSettings
from polyaxon._utils.cli_constants import SYMLINK_MODES
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliRun(BaseCommandTestCase):
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
