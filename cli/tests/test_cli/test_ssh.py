import logging
from pathlib import Path
import pytest
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from polyaxon._cli.ssh import ssh
from polyaxon.exceptions import PolyaxonClientException
from tests.test_cli.utils import BaseCommandTestCase


RUN_UUID = "019e3c01-0000-7000-8000-000000000000"


@pytest.mark.cli_mark
class TestCliSsh(BaseCommandTestCase):
    def setUp(self):
        super().setUp()
        self.project_run = patch(
            "polyaxon._cli.ssh.get_project_run_or_local",
            return_value=("owner", None, "project", RUN_UUID),
        )
        self.client_class = patch("polyaxon._cli.ssh.SandboxClient")
        self.prepare = patch("polyaxon._cli.ssh.prepare_ssh_access")
        self.known_hosts = patch("polyaxon._cli.ssh.write_known_hosts_entry")
        self.tunnel_client = patch("polyaxon._cli.ssh.SandboxSshTunnelClient")
        self.tunnel_runner = patch("polyaxon._cli.ssh.run_tunnel")
        self.ensure_keypair = patch(
            "polyaxon._cli.ssh.ensure_local_keypair",
            return_value=Path("/tmp/polyaxon_sandbox_ed25519"),
        )
        self.ssh_call = patch("polyaxon._cli.ssh.subprocess.call", return_value=0)
        self.resolve_identity = patch(
            "polyaxon._cli.ssh.resolve_identity_file",
            return_value=Path("/tmp/polyaxon_sandbox_ed25519"),
        )
        self.resolve_known_hosts = patch(
            "polyaxon._cli.ssh.resolve_known_hosts_file",
            return_value=Path("/tmp/polyaxon_known_hosts"),
        )
        self.get_project_run_or_local = self.project_run.start()
        self.sandbox_client_class = self.client_class.start()
        self.prepare_ssh_access = self.prepare.start()
        self.write_known_hosts_entry = self.known_hosts.start()
        self.ssh_tunnel_client_class = self.tunnel_client.start()
        self.run_tunnel = self.tunnel_runner.start()
        self.ensure_local_keypair = self.ensure_keypair.start()
        self.subprocess_call = self.ssh_call.start()
        self.resolve_identity_file = self.resolve_identity.start()
        self.resolve_known_hosts_file = self.resolve_known_hosts.start()
        self.client = MagicMock()
        self.sandbox_client_class.return_value = self.client
        self.client._resolve_namespace.return_value = "sandbox-ns"
        self.client._sandbox_url.return_value = (
            "http://polyaxon.test/sandbox/v1/sandbox-ns/owner/project/runs/"
            "{}/ssh/tunnel".format(RUN_UUID)
        )
        self.client.client.config.get_full_headers.return_value = {
            "authorization": "Bearer token"
        }
        self.ssh_tunnel_client = MagicMock()
        self.ssh_tunnel_client_class.return_value = self.ssh_tunnel_client
        self.run_tunnel.return_value = 0
        self.prepare_ssh_access.return_value = SimpleNamespace(
            identity_file=Path("/tmp/polyaxon_sandbox_ed25519"),
            public_key="ssh-ed25519 AAA polyaxon",
            host_public_key="ssh-ed25519 HOST sandbox",
        )
        self.addCleanup(self.project_run.stop)
        self.addCleanup(self.client_class.stop)
        self.addCleanup(self.prepare.stop)
        self.addCleanup(self.known_hosts.stop)
        self.addCleanup(self.tunnel_client.stop)
        self.addCleanup(self.tunnel_runner.stop)
        self.addCleanup(self.ensure_keypair.stop)
        self.addCleanup(self.ssh_call.stop)
        self.addCleanup(self.resolve_identity.stop)
        self.addCleanup(self.resolve_known_hosts.stop)

    def test_commands_are_registered(self):
        from polyaxon.cli import cli

        assert cli.commands["ssh"].name == "ssh"
        assert ssh.commands["connect"].name == "connect"

    def test_group_options_are_not_supported(self):
        result = self.runner.invoke(
            ssh,
            ["-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 2
        self.ensure_local_keypair.assert_not_called()
        self.subprocess_call.assert_not_called()

    def test_connect_builds_exact_ssh_argv(self):
        result = self.runner.invoke(
            ssh,
            ["connect", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 0
        self.ensure_local_keypair.assert_called_once_with(None)
        self.resolve_known_hosts_file.assert_called_once_with(None)
        self.subprocess_call.assert_called_once_with(
            [
                "ssh",
                "-o",
                "User=root",
                "-o",
                "IdentityFile=/tmp/polyaxon_sandbox_ed25519",
                "-o",
                "IdentitiesOnly=yes",
                "-o",
                "UserKnownHostsFile=/tmp/polyaxon_known_hosts",
                "-o",
                "StrictHostKeyChecking=yes",
                "-o",
                (
                    "ProxyCommand=polyaxon ssh tunnel -p owner/project -uid {} "
                    "--identity-file /tmp/polyaxon_sandbox_ed25519 "
                    "--known-hosts-file /tmp/polyaxon_known_hosts"
                ).format(RUN_UUID),
                "polyaxon-{}".format(RUN_UUID),
            ]
        )
        self.prepare_ssh_access.assert_not_called()

    def test_connect_forwards_custom_identity_and_known_hosts(self):
        self.ensure_local_keypair.return_value = Path("/tmp/id_ed25519")
        self.resolve_known_hosts_file.return_value = Path("/tmp/known_hosts")

        result = self.runner.invoke(
            ssh,
            [
                "connect",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--identity-file",
                "/tmp/id_ed25519",
                "--known-hosts-file",
                "/tmp/known_hosts",
            ],
        )

        assert result.exit_code == 0
        self.ensure_local_keypair.assert_called_once_with("/tmp/id_ed25519")
        self.resolve_known_hosts_file.assert_called_once_with("/tmp/known_hosts")
        self.subprocess_call.assert_called_once_with(
            [
                "ssh",
                "-o",
                "User=root",
                "-o",
                "IdentityFile=/tmp/id_ed25519",
                "-o",
                "IdentitiesOnly=yes",
                "-o",
                "UserKnownHostsFile=/tmp/known_hosts",
                "-o",
                "StrictHostKeyChecking=yes",
                "-o",
                (
                    "ProxyCommand=polyaxon ssh tunnel -p owner/project -uid {} "
                    "--identity-file /tmp/id_ed25519 "
                    "--known-hosts-file /tmp/known_hosts"
                ).format(RUN_UUID),
                "polyaxon-{}".format(RUN_UUID),
            ]
        )

    def test_connect_propagates_ssh_exit_code(self):
        self.subprocess_call.return_value = 7

        result = self.runner.invoke(
            ssh,
            ["connect", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 7

    def test_connect_handles_local_key_errors_before_ssh(self):
        self.ensure_local_keypair.side_effect = PolyaxonClientException("bad key")

        result = self.runner.invoke(
            ssh,
            ["connect", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert "bad key" in result.output
        self.subprocess_call.assert_not_called()

    def test_connect_handles_subprocess_launch_errors(self):
        self.subprocess_call.side_effect = OSError("missing ssh")

        result = self.runner.invoke(
            ssh,
            ["connect", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert "missing ssh" in result.output

    def test_setup_prepares_ssh_access(self):
        result = self.runner.invoke(
            ssh,
            ["setup", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 0
        assert "SSH access prepared" in result.output
        assert "IdentityFile /tmp/polyaxon_sandbox_ed25519" in result.output
        assert "UserKnownHostsFile /tmp/polyaxon_known_hosts" in result.output
        self.sandbox_client_class.assert_called_once_with(
            owner="owner",
            project="project",
            run_uuid=RUN_UUID,
            manual_exceptions_handling=True,
        )
        self.prepare_ssh_access.assert_called_once_with(
            client=self.client,
            identity_file=None,
            timeout_ms=30_000,
        )
        self.resolve_known_hosts_file.assert_called_once_with(None)
        self.write_known_hosts_entry.assert_called_once_with(
            path=Path("/tmp/polyaxon_known_hosts"),
            alias="polyaxon-{}".format(RUN_UUID),
            host_public_key="ssh-ed25519 HOST sandbox",
        )

    def test_setup_forwards_identity_file_and_timeout(self):
        result = self.runner.invoke(
            ssh,
            [
                "setup",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--identity-file",
                "/tmp/id_ed25519",
                "--known-hosts-file",
                "/tmp/known_hosts",
                "--timeout-ms",
                "1000",
            ],
        )

        assert result.exit_code == 0
        self.prepare_ssh_access.assert_called_once_with(
            client=self.client,
            identity_file="/tmp/id_ed25519",
            timeout_ms=1000,
        )
        self.resolve_known_hosts_file.assert_called_once_with("/tmp/known_hosts")

    def test_setup_handles_errors(self):
        self.prepare_ssh_access.side_effect = PolyaxonClientException("bad ssh")

        result = self.runner.invoke(
            ssh,
            ["setup", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert "bad ssh" in result.output
        self.write_known_hosts_entry.assert_not_called()

    def test_setup_handles_known_hosts_errors_after_prepare(self):
        self.write_known_hosts_entry.side_effect = OSError("bad known_hosts")

        result = self.runner.invoke(
            ssh,
            ["setup", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert "bad known_hosts" in result.output
        self.prepare_ssh_access.assert_called_once_with(
            client=self.client,
            identity_file=None,
            timeout_ms=30_000,
        )
        self.write_known_hosts_entry.assert_called_once_with(
            path=Path("/tmp/polyaxon_known_hosts"),
            alias="polyaxon-{}".format(RUN_UUID),
            host_public_key="ssh-ed25519 HOST sandbox",
        )

    def test_config_prints_proxy_command(self):
        result = self.runner.invoke(
            ssh,
            ["config", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 0
        assert "Host polyaxon-{}".format(RUN_UUID) in result.output
        assert "HostName polyaxon-{}".format(RUN_UUID) in result.output
        assert "User root" in result.output
        assert "IdentityFile /tmp/polyaxon_sandbox_ed25519" in result.output
        assert "IdentitiesOnly yes" in result.output
        assert "UserKnownHostsFile /tmp/polyaxon_known_hosts" in result.output
        assert "StrictHostKeyChecking yes" in result.output
        assert (
            "ProxyCommand polyaxon ssh tunnel -p owner/project -uid {} "
            "--identity-file /tmp/polyaxon_sandbox_ed25519 "
            "--known-hosts-file /tmp/polyaxon_known_hosts".format(RUN_UUID)
            in result.output
        )
        self.resolve_identity_file.assert_called_once_with(None)
        self.resolve_known_hosts_file.assert_called_once_with(None)
        self.sandbox_client_class.assert_not_called()
        self.prepare_ssh_access.assert_not_called()

    def test_config_forwards_identity_file(self):
        self.resolve_identity_file.return_value = Path("/tmp/id_ed25519")
        self.resolve_known_hosts_file.return_value = Path("/tmp/known_hosts")

        result = self.runner.invoke(
            ssh,
            [
                "config",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--identity-file",
                "/tmp/id_ed25519",
                "--known-hosts-file",
                "/tmp/known_hosts",
            ],
        )

        assert result.exit_code == 0
        assert "IdentityFile /tmp/id_ed25519" in result.output
        assert "UserKnownHostsFile /tmp/known_hosts" in result.output
        assert (
            "--identity-file /tmp/id_ed25519 --known-hosts-file /tmp/known_hosts"
        ) in result.output
        self.resolve_identity_file.assert_called_once_with("/tmp/id_ed25519")
        self.resolve_known_hosts_file.assert_called_once_with("/tmp/known_hosts")

    def test_config_handles_resolution_errors(self):
        self.get_project_run_or_local.side_effect = PolyaxonClientException("bad run")

        result = self.runner.invoke(
            ssh,
            ["config", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert "bad run" in result.output

    def test_tunnel_prepares_access_before_opening_bridge(self):
        events = []

        def prepare_access(**kwargs):
            events.append("setup")
            return SimpleNamespace(
                identity_file=Path("/tmp/polyaxon_sandbox_ed25519"),
                public_key="ssh-ed25519 AAA polyaxon",
                host_public_key="ssh-ed25519 HOST sandbox",
            )

        def write_known_hosts(**kwargs):
            events.append("known_hosts")

        def open_tunnel(**kwargs):
            events.append("connect")
            return self.ssh_tunnel_client

        def bridge(**kwargs):
            events.append("bridge")
            return 0

        self.prepare_ssh_access.side_effect = prepare_access
        self.write_known_hosts_entry.side_effect = write_known_hosts
        self.ssh_tunnel_client_class.side_effect = open_tunnel
        self.run_tunnel.side_effect = bridge

        result = self.runner.invoke(
            ssh,
            ["tunnel", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 0
        assert events == ["setup", "known_hosts", "connect", "bridge"]
        self.sandbox_client_class.assert_called_once_with(
            owner="owner",
            project="project",
            run_uuid=RUN_UUID,
            manual_exceptions_handling=True,
        )
        self.prepare_ssh_access.assert_called_once_with(
            client=self.client,
            identity_file=None,
        )
        self.resolve_known_hosts_file.assert_called_once_with(None)
        self.write_known_hosts_entry.assert_called_once_with(
            path=Path("/tmp/polyaxon_known_hosts"),
            alias="polyaxon-{}".format(RUN_UUID),
            host_public_key="ssh-ed25519 HOST sandbox",
        )
        self.client._resolve_namespace.assert_called_once_with()
        self.client._sandbox_url.assert_called_once_with(
            "sandbox-ns",
            "ssh/tunnel",
        )
        self.client.client.config.get_full_headers.assert_called_once_with(
            headers=None,
            auth_key="authorization",
        )
        self.ssh_tunnel_client_class.assert_called_once_with(
            url=(
                "ws://polyaxon.test/sandbox/v1/sandbox-ns/owner/project/runs/"
                "{}/ssh/tunnel".format(RUN_UUID)
            ),
            headers={"authorization": "Bearer token"},
        )
        self.run_tunnel.assert_called_once()

    def test_tunnel_passes_click_binary_streams_to_bridge(self):
        streams = {}

        def bridge(**kwargs):
            streams["client"] = kwargs["client"] is self.ssh_tunnel_client
            streams["stdin"] = kwargs["stdin"] is sys.stdin.buffer
            streams["stdout"] = kwargs["stdout"] is sys.stdout.buffer
            streams["stderr"] = kwargs["stderr"] is sys.stderr
            return 0

        self.run_tunnel.side_effect = bridge

        result = self.runner.invoke(
            ssh,
            ["tunnel", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 0
        assert streams == {
            "client": True,
            "stdin": True,
            "stdout": True,
            "stderr": True,
        }

    def test_tunnel_forwards_identity_and_known_hosts_files(self):
        result = self.runner.invoke(
            ssh,
            [
                "tunnel",
                "-p",
                "owner/project",
                "-uid",
                RUN_UUID,
                "--identity-file",
                "/tmp/id_ed25519",
                "--known-hosts-file",
                "/tmp/known_hosts",
            ],
        )

        assert result.exit_code == 0
        self.prepare_ssh_access.assert_called_once_with(
            client=self.client,
            identity_file="/tmp/id_ed25519",
        )
        self.resolve_known_hosts_file.assert_called_once_with("/tmp/known_hosts")

    def test_tunnel_handles_setup_errors(self):
        self.prepare_ssh_access.side_effect = PolyaxonClientException("bad ssh")

        result = CliRunner(mix_stderr=False).invoke(
            ssh,
            ["tunnel", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert "polyaxon ssh tunnel: setup: bad ssh" in result.stderr
        self.write_known_hosts_entry.assert_not_called()
        self.ssh_tunnel_client_class.assert_not_called()
        self.run_tunnel.assert_not_called()

    def test_tunnel_handles_known_hosts_errors(self):
        self.write_known_hosts_entry.side_effect = OSError("bad known_hosts")

        result = CliRunner(mix_stderr=False).invoke(
            ssh,
            ["tunnel", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert "polyaxon ssh tunnel: known_hosts: bad known_hosts" in result.stderr
        self.ssh_tunnel_client_class.assert_not_called()
        self.run_tunnel.assert_not_called()

    def test_tunnel_handles_connect_errors(self):
        self.ssh_tunnel_client_class.side_effect = PolyaxonClientException(
            "handshake failed"
        )

        result = CliRunner(mix_stderr=False).invoke(
            ssh,
            ["tunnel", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert "polyaxon ssh tunnel: connect: handshake failed" in result.stderr
        self.run_tunnel.assert_not_called()

    def test_tunnel_propagates_bridge_exit_code(self):
        self.run_tunnel.return_value = 7

        result = CliRunner(mix_stderr=False).invoke(
            ssh,
            ["tunnel", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 7
        assert result.stdout == ""

    def test_tunnel_suppresses_stdout_bound_logging_before_bridge(self):
        root_logger = logging.getLogger()
        previous_level = root_logger.level
        root_logger.setLevel(logging.DEBUG)

        def prepare_access(**kwargs):
            handler = logging.StreamHandler(sys.stdout)
            root_logger.addHandler(handler)
            try:
                root_logger.warning("stdout corruption")
            finally:
                root_logger.removeHandler(handler)
            return SimpleNamespace(
                identity_file=Path("/tmp/polyaxon_sandbox_ed25519"),
                public_key="ssh-ed25519 AAA polyaxon",
                host_public_key="ssh-ed25519 HOST sandbox",
            )

        self.prepare_ssh_access.side_effect = prepare_access

        try:
            result = CliRunner(mix_stderr=False).invoke(
                ssh,
                ["tunnel", "-p", "owner/project", "-uid", RUN_UUID],
            )
        finally:
            root_logger.setLevel(previous_level)

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_tunnel_restores_logging_before_bridge(self):
        previous_disable_level = logging.root.manager.disable
        disable_level = {}

        def bridge(**kwargs):
            disable_level["value"] = logging.root.manager.disable
            return 0

        self.run_tunnel.side_effect = bridge

        result = self.runner.invoke(
            ssh,
            ["tunnel", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 0
        assert disable_level["value"] == previous_disable_level

    def test_tunnel_is_hidden_from_help(self):
        result = self.runner.invoke(ssh, ["--help"])

        assert result.exit_code == 0
        assert "connect" in result.output
        assert "setup" in result.output
        assert "config" in result.output
        assert "tunnel" not in result.output

    def test_only_connect_invokes_ssh_subprocess(self):
        for command in ["setup", "config", "tunnel"]:
            result = self.runner.invoke(
                ssh,
                [command, "-p", "owner/project", "-uid", RUN_UUID],
            )
            assert result.exit_code == 0

        self.subprocess_call.assert_not_called()

        result = self.runner.invoke(
            ssh,
            ["connect", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 0
        self.subprocess_call.assert_called_once()
