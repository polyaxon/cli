from mock import patch
from pathlib import Path
import pytest
import tempfile

from polyaxon._cli.init import init
from polyaxon._cli.operations import ops
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._managers.run import RunConfigManager
from polyaxon._sdk.schemas.v1_project import V1Project
from polyaxon._sdk.schemas.v1_run import V1Run
from tests.test_cli.utils import BaseCommandTestCase


RUN_UUID = "8aac02e3a62a4f0aaa257c59da5eab80"
K8S_EXIT_7 = (
    '{"status":"Failure","details":{"causes":[{"reason":"ExitCode","message":"7"}]}}'
)


@pytest.mark.cli_mark
class TestCliCachedRunContext(BaseCommandTestCase):
    def setUp(self):
        super().setUp()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.local_cache = Path(directory.name) / "local" / ".polyaxon"
        self.global_cache = Path(directory.name) / "global" / ".polyaxon"
        for manager in (ProjectConfigManager, RunConfigManager):
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

    def assert_conflicting_context(self, result, run_path):
        assert result.exit_code != 0
        assert "owner/project-a" in result.output
        assert "owner/project-b" in result.output
        assert RUN_UUID in result.output
        assert str(run_path) in result.output

    @patch("polyaxon._client.run.RunClient")
    def test_statuses_rejects_explicit_project_conflict(self, run_client):
        result = self.runner.invoke(ops, ["--project", "owner/project-b", "statuses"])

        self.assert_conflicting_context(result, self.local_cache / ".run")
        run_client.assert_not_called()

    @patch("polyaxon._client.run.RunClient")
    def test_stop_rejects_explicit_project_conflict(self, run_client):
        result = self.runner.invoke(
            ops, ["--project", "owner/project-b", "stop", "--yes"]
        )

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

        result = self.runner.invoke(ops, ["statuses"])

        self.assert_conflicting_context(result, self.local_cache / ".run")
        run_client.assert_not_called()


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
    @patch("polyaxon.client.RunClient.list")
    def test_list_runs(self, list_runs):
        self.runner.invoke(ops, ["-p", "admin/foo", "ls"])
        assert list_runs.call_count == 1

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
    @patch("polyaxon._env_vars.getters.get_project_run_or_local")
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
    @patch("polyaxon._env_vars.getters.get_project_run_or_local")
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
