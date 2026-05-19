from mock import MagicMock, patch
import pytest
from types import SimpleNamespace

from polyaxon._cli.sandbox import sandbox
from polyaxon.exceptions import PolyaxonClientException
from tests.test_cli.utils import BaseCommandTestCase


RUN_UUID = "019e3c01-0000-7000-8000-000000000000"


class Stream:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        return iter(self.events)

    def __exit__(self, *exc):
        return False


def make_client():
    client = MagicMock()
    client.run_uuid = RUN_UUID
    client.ping.return_value = SimpleNamespace(status="ok", version="2.16.0")
    client.process.exec.return_value = SimpleNamespace(
        stdout="out\n",
        stderr="err\n",
        exit_code=0,
    )
    client.process.exec_bg.return_value = SimpleNamespace(id="exec-1")
    client.process.exec_stream.return_value = Stream(
        [
            {"type": "stdout", "text": "out\n"},
            {"type": "stderr", "text": "err\n"},
            {"type": "execution_complete", "exit_code": 0},
        ]
    )
    client.process.logs.return_value = SimpleNamespace(data="logs\n")
    client.fs.ls.return_value = SimpleNamespace(
        entries=[
            SimpleNamespace(name="file.txt", type="file", size=5, mode="0644"),
        ]
    )
    client.pty.create.return_value = SimpleNamespace(pty_id="pty-1")
    return client


@pytest.mark.cli_mark
class TestCliSandbox(BaseCommandTestCase):
    def setUp(self):
        super().setUp()
        self.project_run = patch(
            "polyaxon._cli.sandbox.get_project_run_or_local",
            return_value=("owner", None, "project", RUN_UUID),
        )
        self.client_class = patch("polyaxon._cli.sandbox.SandboxClient")
        self.get_project_run_or_local = self.project_run.start()
        self.sandbox_client_class = self.client_class.start()
        self.client = make_client()
        self.sandbox_client_class.return_value = self.client
        self.addCleanup(self.project_run.stop)
        self.addCleanup(self.client_class.stop)

    def test_command_is_registered(self):
        from polyaxon.cli import cli

        assert cli.commands["sandbox"].name == "sandbox"

    def test_ping(self):
        result = self.runner.invoke(
            sandbox,
            ["ping", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 0
        assert "ok" in result.output
        assert "2.16.0" in result.output
        self.sandbox_client_class.assert_called_once_with(
            owner="owner",
            project="project",
            run_uuid=RUN_UUID,
            manual_exceptions_handling=True,
        )

    def test_client_construction_errors_are_handled(self):
        self.sandbox_client_class.side_effect = PolyaxonClientException("bad run")
        cases = [
            ["ping", "-p", "owner/project", "-uid", RUN_UUID],
            ["exec", "-p", "owner/project", "-uid", RUN_UUID, "--", "python", "-V"],
            ["shell", "-p", "owner/project", "-uid", RUN_UUID],
            ["logs", "-p", "owner/project", "-uid", RUN_UUID, "exec-1"],
            ["ls", "-p", "owner/project", "-uid", RUN_UUID, "/tmp"],
            [
                "upload",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "local.txt",
                "/tmp/remote.txt",
            ],
            [
                "download",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "/tmp/remote.txt",
                "local.txt",
            ],
        ]
        for args in cases:
            with self.subTest(command=args[0]):
                result = self.runner.invoke(sandbox, args)

                assert result.exit_code == 1
                assert "bad run" in result.output

    def test_namespace_is_not_exposed(self):
        result = self.runner.invoke(
            sandbox,
            ["ping", "-p", "owner/project", "-uid", RUN_UUID, "--namespace", "ns"],
        )

        assert result.exit_code != 0
        assert "No such option" in result.output
        assert "--namespace" in result.output
        self.sandbox_client_class.assert_not_called()

    def test_exec_rejects_namespace_before_command_separator(self):
        result = self.runner.invoke(
            sandbox,
            [
                "exec",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--namespace",
                "ns",
                "--",
                "python",
                "-V",
            ],
        )

        assert result.exit_code != 0
        assert "No such option" in result.output
        assert "--namespace" in result.output
        self.client.process.exec.assert_not_called()

    def test_exec_requires_separator(self):
        result = self.runner.invoke(
            sandbox,
            ["exec", "-p", "owner/project", "-uid", RUN_UUID, "ls", "-la"],
        )

        assert result.exit_code != 0
        assert "command required after --" in result.output
        self.client.process.exec.assert_not_called()

    def test_exec_rejects_stream_and_detach(self):
        result = self.runner.invoke(
            sandbox,
            [
                "exec",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--stream",
                "--detach",
                "--",
                "sleep",
                "60",
            ],
        )

        assert result.exit_code != 0
        assert "Use only one of --stream or --detach" in result.output
        self.client.process.exec.assert_not_called()
        self.client.process.exec_bg.assert_not_called()
        self.client.process.exec_stream.assert_not_called()

    def test_exec_one_shot_propagates_exit_code(self):
        self.client.process.exec.return_value = SimpleNamespace(
            stdout="out\n",
            stderr="err\n",
            exit_code=7,
        )

        result = self.runner.invoke(
            sandbox,
            ["exec", "-p", "owner/project", "-uid", RUN_UUID, "--", "python", "-V"],
        )

        assert result.exit_code == 7
        assert "out" in result.output
        self.client.process.exec.assert_called_once_with(
            command=("python", "-V"),
            timeout_ms=None,
        )

    def test_exec_stream_propagates_exit_code(self):
        self.client.process.exec_stream.return_value = Stream(
            [
                {"type": "stdout", "text": "out\n"},
                {"type": "execution_complete", "exit_code": 7},
            ]
        )

        result = self.runner.invoke(
            sandbox,
            [
                "exec",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--stream",
                "--",
                "sh",
                "-lc",
                "echo hi",
            ],
        )

        assert result.exit_code == 7
        assert "out" in result.output
        self.client.process.exec_stream.assert_called_once_with(
            command=("sh", "-lc", "echo hi"),
            timeout_ms=None,
        )

    def test_exec_stream_requires_completion_event(self):
        self.client.process.exec_stream.return_value = Stream(
            [{"type": "stdout", "text": "out\n"}]
        )

        result = self.runner.invoke(
            sandbox,
            ["exec", "-p", "owner/project", "-uid", RUN_UUID, "--stream", "--", "sh"],
        )

        assert result.exit_code == 1
        assert "stream ended without completion event" in result.output

    def test_exec_stream_error_event_exits_one(self):
        self.client.process.exec_stream.return_value = Stream(
            [{"type": "error", "text": "boom\n"}]
        )

        result = self.runner.invoke(
            sandbox,
            ["exec", "-p", "owner/project", "-uid", RUN_UUID, "--stream", "--", "sh"],
        )

        assert result.exit_code == 1
        assert "boom" in result.output

    def test_exec_detach_prints_exec_id(self):
        result = self.runner.invoke(
            sandbox,
            [
                "exec",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--detach",
                "--tag",
                "cli",
                "--",
                "sleep",
                "60",
            ],
        )

        assert result.exit_code == 0
        assert "exec-1" in result.output
        self.client.process.exec_bg.assert_called_once_with(
            command=("sleep", "60"),
            timeout_ms=None,
            tag="cli",
        )

    def test_logs(self):
        result = self.runner.invoke(
            sandbox,
            ["logs", "-p", "owner/project", "-uid", RUN_UUID, "exec-1"],
        )

        assert result.exit_code == 0
        assert "logs" in result.output
        self.client.process.logs.assert_called_once_with(
            "exec-1",
            stream="stdout",
            offset=0,
            max_bytes=None,
        )

    def test_logs_forwards_cursor_options(self):
        result = self.runner.invoke(
            sandbox,
            [
                "logs",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--offset",
                "100",
                "--max-bytes",
                "50",
                "exec-1",
            ],
        )

        assert result.exit_code == 0
        self.client.process.logs.assert_called_once_with(
            "exec-1",
            stream="stdout",
            offset=100,
            max_bytes=50,
        )

    def test_ls(self):
        result = self.runner.invoke(
            sandbox,
            ["ls", "-p", "owner/project", "-uid", RUN_UUID, "--recursive", "/tmp"],
        )

        assert result.exit_code == 0
        assert "file.txt" in result.output
        self.client.fs.ls.assert_called_once_with(
            "/tmp",
            recursive=True,
            max_entries=None,
        )

    def test_shell_starts_default_pty_and_propagates_exit_code(self):
        ws = MagicMock()
        self.client.pty.attach.return_value = ws
        with (
            patch(
                "polyaxon._cli.sandbox.shutil.get_terminal_size",
                return_value=SimpleNamespace(columns=100, lines=30),
            ),
            patch("polyaxon._cli.sandbox.SandboxPseudoTerminal") as terminal,
        ):
            terminal.return_value.start.return_value = 7

            result = self.runner.invoke(
                sandbox,
                ["shell", "-p", "owner/project", "-uid", RUN_UUID],
            )

        assert result.exit_code == 7
        self.client.pty.create.assert_called_once_with(
            command=["sh"],
            cols=100,
            rows=30,
        )
        self.client.pty.attach.assert_called_once_with("pty-1", replay_bytes=0)
        terminal.assert_called_once_with(ws)

    def test_shell_forwards_command_size_and_replay_options(self):
        ws = MagicMock()
        self.client.pty.attach.return_value = ws
        with patch("polyaxon._cli.sandbox.SandboxPseudoTerminal") as terminal:
            terminal.return_value.start.return_value = 0

            result = self.runner.invoke(
                sandbox,
                [
                    "shell",
                    "-p",
                    "owner/project",
                    "-uid",
                    RUN_UUID,
                    "--command",
                    "python -i",
                    "--cols",
                    "120",
                    "--rows",
                    "40",
                    "--replay-bytes",
                    "1024",
                ],
            )

        assert result.exit_code == 0
        self.client.pty.create.assert_called_once_with(
            command=["python", "-i"],
            cols=120,
            rows=40,
        )
        self.client.pty.attach.assert_called_once_with("pty-1", replay_bytes=1024)
        terminal.assert_called_once_with(ws)

    def test_shell_rejects_empty_command(self):
        result = self.runner.invoke(
            sandbox,
            [
                "shell",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--command",
                "",
            ],
        )

        assert result.exit_code == 1
        assert "shell command must not be empty" in result.output
        self.client.pty.create.assert_not_called()

    def test_upload(self):
        result = self.runner.invoke(
            sandbox,
            [
                "upload",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "local.txt",
                "/tmp/remote.txt",
            ],
        )

        assert result.exit_code == 0
        self.client.fs.upload_file.assert_called_once_with(
            local_path="local.txt",
            path="/tmp/remote.txt",
            chunk_size=64 * 1024,
        )
        self.client.fs.download_file.assert_not_called()

    def test_download(self):
        result = self.runner.invoke(
            sandbox,
            [
                "download",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "/tmp/remote.txt",
                "local.txt",
            ],
        )

        assert result.exit_code == 0
        self.client.fs.download_file.assert_called_once_with(
            path="/tmp/remote.txt",
            local_path="local.txt",
            chunk_size=64 * 1024,
        )
        self.client.fs.upload_file.assert_not_called()

    def test_upload_rejects_invalid_remote_path(self):
        cases = [
            ("local.txt", "", "remote path is empty"),
            ("local.txt", "/tmp/", "remote path must include filename"),
            ("local.txt", "relative/path", "path must be absolute"),
        ]
        for path_from, path_to, message in cases:
            with self.subTest(path_from=path_from, path_to=path_to):
                result = self.runner.invoke(
                    sandbox,
                    [
                        "upload",
                        "-p",
                        "owner/project",
                        "-uid",
                        RUN_UUID,
                        path_from,
                        path_to,
                    ],
                )

                assert result.exit_code == 1
                assert message in result.output
                self.client.fs.upload_file.assert_not_called()
                self.client.fs.download_file.assert_not_called()

    def test_upload_rejects_invalid_chunk_size(self):
        result = self.runner.invoke(
            sandbox,
            [
                "upload",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--chunk-size",
                "0",
                "local.txt",
                "/tmp/remote.txt",
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value for '--chunk-size'" in result.output
        self.client.fs.upload_file.assert_not_called()
        self.client.fs.download_file.assert_not_called()

    def test_download_rejects_invalid_remote_path(self):
        cases = [
            ("", "local.txt", "remote path is empty"),
            ("/tmp/", "local.txt", "remote path must include filename"),
            ("relative/path", "local.txt", "path must be absolute"),
        ]
        for path_from, path_to, message in cases:
            with self.subTest(path_from=path_from, path_to=path_to):
                result = self.runner.invoke(
                    sandbox,
                    [
                        "download",
                        "-p",
                        "owner/project",
                        "-uid",
                        RUN_UUID,
                        path_from,
                        path_to,
                    ],
                )

                assert result.exit_code == 1
                assert message in result.output
                self.client.fs.upload_file.assert_not_called()
                self.client.fs.download_file.assert_not_called()
