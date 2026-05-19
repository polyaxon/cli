from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
from typing import Optional

from polyaxon._ssh.constants import (
    DEFAULT_SSH_KEY_PATH,
    POLYAXON_KNOWN_HOSTS_PATH,
    SSH_AUTHORIZED_KEYS_PATH,
    SSH_ETC_PATH,
    SSH_HOST_KEY_PATH,
    SSH_KEY_COMMENT,
)
from polyaxon.exceptions import PolyaxonClientException


SSH_SETUP_TIMEOUT_MS = 30_000

SSH_SETUP_SCRIPT = """
set -eu
mkdir -p {ssh_etc_path}
if [ ! -f {host_key_path} ]; then
  /opt/polyaxon/bin/ssh-keygen -t ed25519 -N "" -f {host_key_path} >/dev/null 2>&1
fi
touch {authorized_keys_path}
chmod 600 {host_key_path} {authorized_keys_path}
pub="$(cat)"
grep -qxF "$pub" {authorized_keys_path} || printf '%s\\n' "$pub" >> {authorized_keys_path}
/opt/polyaxon/bin/ssh-keygen -y -f {host_key_path}
""".strip().format(
    ssh_etc_path=SSH_ETC_PATH,
    host_key_path=SSH_HOST_KEY_PATH,
    authorized_keys_path=SSH_AUTHORIZED_KEYS_PATH,
)


@dataclass(frozen=True)
class SshAccess:
    identity_file: Path
    public_key: str
    host_public_key: str


def resolve_identity_file(identity_file: Optional[str] = None) -> Path:
    return Path(identity_file or DEFAULT_SSH_KEY_PATH).expanduser()


def resolve_known_hosts_file(path: Optional[str] = None) -> Path:
    return Path(path or POLYAXON_KNOWN_HOSTS_PATH).expanduser()


def _public_key_path(identity_file: Path) -> Path:
    return Path("{}{}".format(identity_file, ".pub"))


def _validate_host_public_key(host_public_key: str) -> str:
    value = (host_public_key or "").strip()
    if not value.startswith("ssh-ed25519 "):
        raise PolyaxonClientException("Could not retrieve sandbox host public key.")
    return value


def ensure_local_keypair(identity_file: Optional[str] = None) -> Path:
    path = resolve_identity_file(identity_file)
    if path.exists():
        return path

    if identity_file:
        raise PolyaxonClientException(
            "SSH identity file does not exist: {}".format(path)
        )

    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
        subprocess.check_call(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-N",
                "",
                "-C",
                SSH_KEY_COMMENT,
                "-f",
                str(path),
            ]
        )
    except (OSError, subprocess.CalledProcessError) as e:
        raise PolyaxonClientException(
            "Could not create SSH identity file `{}`: {}".format(path, e)
        ) from e
    return path


def get_public_key(identity_file: Path) -> str:
    public_key_path = _public_key_path(identity_file)
    if public_key_path.exists():
        public_key = public_key_path.read_text(encoding="utf-8").strip()
    else:
        try:
            public_key = (
                subprocess.check_output(["ssh-keygen", "-y", "-f", str(identity_file)])
                .decode("utf-8")
                .strip()
            )
        except (OSError, subprocess.CalledProcessError) as e:
            raise PolyaxonClientException(
                "Could not read SSH public key for `{}`: {}".format(identity_file, e)
            ) from e

    if not public_key:
        raise PolyaxonClientException(
            "SSH public key for `{}` is empty.".format(identity_file)
        )
    return public_key


def build_remote_setup_command():
    return ["sh", "-lc", SSH_SETUP_SCRIPT]


def prepare_ssh_access(
    client,
    identity_file: Optional[str] = None,
    timeout_ms: Optional[int] = SSH_SETUP_TIMEOUT_MS,
) -> SshAccess:
    identity_path = ensure_local_keypair(identity_file=identity_file)
    public_key = get_public_key(identity_path)
    result = client.process.exec(
        command=build_remote_setup_command(),
        stdin="{}\n".format(public_key).encode("utf-8"),
        timeout_ms=timeout_ms,
    )
    exit_code = getattr(result, "exit_code", 0)
    if exit_code:
        message = getattr(result, "stderr", None) or getattr(result, "stdout", None)
        raise PolyaxonClientException(
            "Could not prepare SSH access: {}".format(message or exit_code)
        )
    host_public_key = _validate_host_public_key(getattr(result, "stdout", ""))
    return SshAccess(
        identity_file=identity_path,
        public_key=public_key,
        host_public_key=host_public_key,
    )


def write_known_hosts_entry(path: Path, alias: str, host_public_key: str):
    host_public_key = _validate_host_public_key(host_public_key)
    path = path.expanduser()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)

    prefix = "{} ".format(alias)
    if path.exists():
        lines = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if not line.startswith(prefix)
        ]
    else:
        lines = []
    lines.append("{} {}".format(alias, host_public_key))

    tmp = path.with_name("{}.tmp".format(path.name))
    tmp.write_text("{}\n".format("\n".join(lines)), encoding="utf-8")
    tmp.chmod(0o600)
    os.replace(str(tmp), str(path))
