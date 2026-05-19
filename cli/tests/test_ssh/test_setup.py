from pathlib import Path
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from polyaxon._ssh import setup
from polyaxon._ssh.constants import SSH_AUTHORIZED_KEYS_PATH, SSH_HOST_KEY_PATH
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
        ]
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

    check_output.assert_called_once_with(["ssh-keygen", "-y", "-f", str(identity_file)])


def test_build_remote_setup_command_is_idempotent():
    command = setup.build_remote_setup_command()

    assert command[:2] == ["sh", "-lc"]
    script = command[2]
    assert SSH_HOST_KEY_PATH in script
    assert SSH_AUTHORIZED_KEYS_PATH in script
    assert 'grep -qxF "$pub"' in script
    assert ">> {}".format(SSH_AUTHORIZED_KEYS_PATH) in script


def test_prepare_ssh_access_pushes_public_key_through_sandbox(tmp_path):
    identity_file = tmp_path / "id_ed25519"
    identity_file.write_text("private", encoding="utf-8")
    Path("{}{}".format(identity_file, ".pub")).write_text(
        "ssh-ed25519 CCC user\n",
        encoding="utf-8",
    )
    client = MagicMock()
    client.process.exec.return_value = SimpleNamespace(exit_code=0)

    access = setup.prepare_ssh_access(client, identity_file=str(identity_file))

    assert access.identity_file == identity_file
    assert access.public_key == "ssh-ed25519 CCC user"
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
