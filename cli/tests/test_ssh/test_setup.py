from pathlib import Path
import pytest
import stat
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from polyaxon._ssh import setup
from polyaxon._ssh.constants import (
    POLYAXON_KNOWN_HOSTS_PATH,
    SSH_AUTHORIZED_KEYS_PATH,
    SSH_HOST_KEY_PATH,
)
from polyaxon.exceptions import PolyaxonClientException


def test_ensure_local_keypair_generates_default_key(tmp_path):
    identity_file = tmp_path / ".ssh" / "polyaxon_sandbox_ed25519"

    with (
        patch("polyaxon._ssh.setup.DEFAULT_SSH_KEY_PATH", str(identity_file)),
        patch("polyaxon._ssh.setup.subprocess.check_call") as check_call,
    ):
        path = setup.ensure_local_keypair()

    assert path == identity_file
    assert identity_file.parent.exists()
    check_call.assert_called_once_with(
        [
            "ssh-keygen",
            "-t",
            "ed25519",
            "-N",
            "",
            "-C",
            "polyaxon-sandbox",
            "-f",
            str(identity_file),
        ],
        stdout=setup.subprocess.DEVNULL,
        stderr=setup.subprocess.DEVNULL,
    )


def test_ensure_local_keypair_reuses_existing_key(tmp_path):
    identity_file = tmp_path / "id_ed25519"
    identity_file.write_text("private", encoding="utf-8")

    with patch("polyaxon._ssh.setup.subprocess.check_call") as check_call:
        path = setup.ensure_local_keypair(str(identity_file))

    assert path == identity_file
    check_call.assert_not_called()


def test_ensure_local_keypair_rejects_missing_explicit_key(tmp_path):
    identity_file = tmp_path / "missing"

    with pytest.raises(PolyaxonClientException) as ctx:
        setup.ensure_local_keypair(str(identity_file))

    assert "does not exist" in str(ctx.value)


def test_get_public_key_reads_pub_file(tmp_path):
    identity_file = tmp_path / "id_ed25519"
    public_key_file = Path("{}{}".format(identity_file, ".pub"))
    public_key_file.write_text("ssh-ed25519 AAA test\n", encoding="utf-8")

    with patch("polyaxon._ssh.setup.subprocess.check_output") as check_output:
        assert setup.get_public_key(identity_file) == "ssh-ed25519 AAA test"

    check_output.assert_not_called()


def test_get_public_key_derives_from_private_key_when_pub_file_missing(tmp_path):
    identity_file = tmp_path / "id_ed25519"
    identity_file.write_text("private", encoding="utf-8")

    with patch(
        "polyaxon._ssh.setup.subprocess.check_output",
        return_value=b"ssh-ed25519 BBB derived\n",
    ) as check_output:
        assert setup.get_public_key(identity_file) == "ssh-ed25519 BBB derived"

    check_output.assert_called_once_with(
        ["ssh-keygen", "-y", "-f", str(identity_file)],
        stderr=setup.subprocess.DEVNULL,
    )


def test_build_remote_setup_command_is_idempotent():
    command = setup.build_remote_setup_command()

    assert command[:2] == ["sh", "-lc"]
    script = command[2]
    assert SSH_HOST_KEY_PATH in script
    assert SSH_AUTHORIZED_KEYS_PATH in script
    assert ">/dev/null 2>&1" in script
    assert 'grep -qxF "$pub"' in script
    assert ">> {}".format(SSH_AUTHORIZED_KEYS_PATH) in script
    assert script.endswith(
        "/opt/polyaxon/bin/ssh-keygen -y -f {}".format(SSH_HOST_KEY_PATH)
    )


def test_prepare_ssh_access_pushes_public_key_through_sandbox(tmp_path):
    identity_file = tmp_path / "id_ed25519"
    identity_file.write_text("private", encoding="utf-8")
    Path("{}{}".format(identity_file, ".pub")).write_text(
        "ssh-ed25519 CCC user\n",
        encoding="utf-8",
    )
    client = MagicMock()
    client.process.exec.return_value = SimpleNamespace(
        exit_code=0,
        stdout="ssh-ed25519 HOST sandbox\n",
    )

    access = setup.prepare_ssh_access(client, identity_file=str(identity_file))

    assert access.identity_file == identity_file
    assert access.public_key == "ssh-ed25519 CCC user"
    assert access.host_public_key == "ssh-ed25519 HOST sandbox"
    client.process.exec.assert_called_once_with(
        command=setup.build_remote_setup_command(),
        stdin=b"ssh-ed25519 CCC user\n",
        timeout_ms=setup.SSH_SETUP_TIMEOUT_MS,
    )


def test_prepare_ssh_access_raises_on_remote_failure(tmp_path):
    identity_file = tmp_path / "id_ed25519"
    identity_file.write_text("private", encoding="utf-8")
    Path("{}{}".format(identity_file, ".pub")).write_text(
        "ssh-ed25519 DDD user\n",
        encoding="utf-8",
    )
    client = MagicMock()
    client.process.exec.return_value = SimpleNamespace(exit_code=1, stderr="boom")

    with pytest.raises(PolyaxonClientException) as ctx:
        setup.prepare_ssh_access(client, identity_file=str(identity_file))

    assert "boom" in str(ctx.value)


def test_prepare_ssh_access_rejects_missing_host_public_key(tmp_path):
    identity_file = tmp_path / "id_ed25519"
    identity_file.write_text("private", encoding="utf-8")
    Path("{}{}".format(identity_file, ".pub")).write_text(
        "ssh-ed25519 EEE user\n",
        encoding="utf-8",
    )
    client = MagicMock()
    client.process.exec.return_value = SimpleNamespace(exit_code=0, stdout="")

    with pytest.raises(PolyaxonClientException) as ctx:
        setup.prepare_ssh_access(client, identity_file=str(identity_file))

    assert "host public key" in str(ctx.value)


def test_resolve_known_hosts_file_defaults_to_polyaxon_managed_path():
    assert (
        setup.resolve_known_hosts_file() == Path(POLYAXON_KNOWN_HOSTS_PATH).expanduser()
    )


def test_write_known_hosts_entry_creates_file(tmp_path):
    known_hosts = tmp_path / ".polyaxon" / "known_hosts"

    setup.write_known_hosts_entry(
        path=known_hosts,
        alias="polyaxon-run",
        host_public_key="ssh-ed25519 HOST",
    )

    assert known_hosts.read_text(encoding="utf-8") == "polyaxon-run ssh-ed25519 HOST\n"
    assert stat.S_IMODE(known_hosts.stat().st_mode) == 0o600
    assert stat.S_IMODE(known_hosts.parent.stat().st_mode) == 0o700


def test_write_known_hosts_entry_replaces_alias_and_preserves_others(tmp_path):
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text(
        "\n".join(
            [
                "polyaxon-run ssh-ed25519 OLD",
                "polyaxon-other ssh-ed25519 OTHER",
                "polyaxon-run-suffix ssh-ed25519 SUFFIX",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    setup.write_known_hosts_entry(
        path=known_hosts,
        alias="polyaxon-run",
        host_public_key="ssh-ed25519 NEW",
    )

    assert known_hosts.read_text(encoding="utf-8").splitlines() == [
        "polyaxon-other ssh-ed25519 OTHER",
        "polyaxon-run-suffix ssh-ed25519 SUFFIX",
        "polyaxon-run ssh-ed25519 NEW",
    ]


def test_write_known_hosts_entry_rejects_invalid_host_key(tmp_path):
    with pytest.raises(PolyaxonClientException):
        setup.write_known_hosts_entry(
            path=tmp_path / "known_hosts",
            alias="polyaxon-run",
            host_public_key="not-a-key",
        )
