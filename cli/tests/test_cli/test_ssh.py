from pathlib import Path
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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
        self.resolve_identity_file = self.resolve_identity.start()
        self.resolve_known_hosts_file = self.resolve_known_hosts.start()
        self.client = MagicMock()
        self.sandbox_client_class.return_value = self.client
        self.prepare_ssh_access.return_value = SimpleNamespace(
            identity_file=Path("/tmp/polyaxon_sandbox_ed25519"),
            public_key="ssh-ed25519 AAA polyaxon",
            host_public_key="ssh-ed25519 HOST sandbox",
        )
        self.addCleanup(self.project_run.stop)
        self.addCleanup(self.client_class.stop)
        self.addCleanup(self.prepare.stop)
        self.addCleanup(self.known_hosts.stop)
        self.addCleanup(self.resolve_identity.stop)
        self.addCleanup(self.resolve_known_hosts.stop)

    def test_command_is_registered(self):
        from polyaxon.cli import cli

        assert cli.commands["ssh"].name == "ssh"

    def test_setup_prepares_ssh_access(self):
        result = self.runner.invoke(
            ssh,
            ["setup", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 0
        assert "SSH access prepared" in result.output
        assert "IdentityFile /tmp/polyaxon_sandbox_ed25519" in result.output
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

    def test_setup_handles_errors(self):
        self.prepare_ssh_access.side_effect = PolyaxonClientException("bad ssh")

        result = self.runner.invoke(
            ssh,
            ["setup", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert "bad ssh" in result.output

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
        assert "UserKnownHostsFile /tmp/polyaxon_known_hosts" in result.output
        assert "StrictHostKeyChecking yes" in result.output
        assert (
            "ProxyCommand polyaxon ssh tunnel -p owner/project -uid {} "
            "--identity-file /tmp/polyaxon_sandbox_ed25519".format(RUN_UUID)
            in result.output
        )
        self.resolve_identity_file.assert_called_once_with(None)
        self.resolve_known_hosts_file.assert_called_once_with(None)
        self.sandbox_client_class.assert_not_called()
        self.prepare_ssh_access.assert_not_called()

    def test_config_forwards_identity_file(self):
        self.resolve_identity_file.return_value = Path("/tmp/id_ed25519")

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
        assert "UserKnownHostsFile /tmp/polyaxon_known_hosts" in result.output
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

    def test_tunnel_prepares_access_before_not_implemented_error(self):
        result = self.runner.invoke(
            ssh,
            ["tunnel", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert "SSH tunnel transport is not implemented yet" in result.output
        assert "Setup completed" in result.output
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

    def test_tunnel_handles_setup_errors(self):
        self.prepare_ssh_access.side_effect = PolyaxonClientException("bad ssh")

        result = self.runner.invoke(
            ssh,
            ["tunnel", "-p", "owner/project", "-uid", RUN_UUID],
        )

        assert result.exit_code == 1
        assert "bad ssh" in result.output
        self.write_known_hosts_entry.assert_not_called()

    def test_tunnel_is_hidden_from_help(self):
        result = self.runner.invoke(ssh, ["--help"])

        assert result.exit_code == 0
        assert "setup" in result.output
        assert "config" in result.output
        assert "tunnel" not in result.output
