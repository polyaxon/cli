from contextlib import contextmanager
import logging
import shlex
import subprocess
import sys

import click
from urllib3.exceptions import HTTPError

from clipped.formatting import Printer
from clipped.utils.http import to_ws_url
from polyaxon._cli.errors import handle_cli_error
from polyaxon._cli.options import OPTIONS_PROJECT, OPTIONS_RUN_UID
from polyaxon._client.transport.ssh_tunnel import SandboxSshTunnelClient
from polyaxon._env_vars.getters import get_project_run_or_local
from polyaxon._ssh import (
    ensure_local_keypair,
    prepare_ssh_access,
    resolve_identity_file,
    resolve_known_hosts_file,
    write_known_hosts_entry,
)
from polyaxon._ssh.tunnel import run_tunnel
from polyaxon.client import SandboxClient
from polyaxon.exceptions import ApiException, PolyaxonClientException
from polyaxon.logger import clean_outputs


def _sandbox_client(project, uid):
    owner, _, project_name, run_uuid = get_project_run_or_local(
        project, uid, is_cli=True
    )
    return SandboxClient(
        owner=owner,
        project=project_name,
        run_uuid=run_uuid,
        manual_exceptions_handling=True,
    )


def _ssh_tunnel_url(client):
    return to_ws_url(client._sandbox_url(client._resolve_namespace(), "ssh/tunnel"))


def _ssh_tunnel_headers(client):
    return client.client.config.get_full_headers(
        headers=None,
        auth_key="authorization",
    )


def _write_tunnel_error(stage, error):
    click.echo("polyaxon ssh tunnel: {}: {}".format(stage, error), err=True)


@contextmanager
def _disable_tunnel_logging():
    previous_disable_level = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(previous_disable_level)


def _proxy_command(project_ref, run_uuid, identity_file, known_hosts_file):
    return (
        "polyaxon ssh tunnel -p {} -uid {} --identity-file {} --known-hosts-file {}"
    ).format(
        shlex.quote(project_ref),
        shlex.quote(run_uuid),
        shlex.quote(str(identity_file)),
        shlex.quote(str(known_hosts_file)),
    )


def _ssh_target(run_uuid):
    return "polyaxon-{}".format(run_uuid)


def _ssh_connect_argv(project_ref, run_uuid, identity_file, known_hosts_file):
    return [
        "ssh",
        "-o",
        "User=root",
        "-o",
        "IdentityFile={}".format(identity_file),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "UserKnownHostsFile={}".format(known_hosts_file),
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        "ProxyCommand={}".format(
            _proxy_command(
                project_ref=project_ref,
                run_uuid=run_uuid,
                identity_file=identity_file,
                known_hosts_file=known_hosts_file,
            )
        ),
        _ssh_target(run_uuid),
    ]


def _ssh_config(project_ref, run_uuid, identity_file, known_hosts_file):
    host = _ssh_target(run_uuid)
    return "\n".join(
        [
            "Host {}".format(host),
            "  HostName {}".format(host),
            "  User root",
            "  IdentityFile {}".format(identity_file),
            "  IdentitiesOnly yes",
            "  UserKnownHostsFile {}".format(known_hosts_file),
            "  StrictHostKeyChecking yes",
            "  ProxyCommand {}".format(
                _proxy_command(
                    project_ref=project_ref,
                    run_uuid=run_uuid,
                    identity_file=identity_file,
                    known_hosts_file=known_hosts_file,
                )
            ),
        ]
    )


@click.group()
@clean_outputs
def ssh():
    """SSH access for sandbox-enabled runs."""


@ssh.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--identity-file",
    type=click.Path(dir_okay=False),
    help="SSH private key to use. Defaults to Polyaxon's managed sandbox key.",
)
@click.option(
    "--known-hosts-file",
    type=click.Path(dir_okay=False),
    help="Known hosts file to use. Defaults to Polyaxon's managed file.",
)
@clean_outputs
def connect(project, uid, identity_file, known_hosts_file):
    """Connect to a sandbox run over SSH."""
    try:
        owner, _, project_name, run_uuid = get_project_run_or_local(
            project, uid, is_cli=True
        )
        identity_path = ensure_local_keypair(identity_file)
        known_hosts_path = resolve_known_hosts_file(known_hosts_file)
        exit_code = subprocess.call(
            _ssh_connect_argv(
                project_ref="{}/{}".format(owner, project_name),
                run_uuid=run_uuid,
                identity_file=identity_path,
                known_hosts_file=known_hosts_path,
            )
        )
    except (OSError, PolyaxonClientException) as e:
        handle_cli_error(
            e,
            "Could not start SSH connection for run `{}`.".format(uid),
            sys_exit=True,
        )
        return
    raise click.exceptions.Exit(exit_code)


@ssh.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--identity-file",
    type=click.Path(dir_okay=False),
    help="SSH private key to use. Defaults to Polyaxon's managed sandbox key.",
)
@click.option(
    "--known-hosts-file",
    type=click.Path(dir_okay=False),
    help="Known hosts file to use. Defaults to Polyaxon's managed file.",
)
@click.option(
    "--timeout-ms",
    type=click.IntRange(min=1),
    default=30_000,
    show_default=True,
    help="Remote SSH setup timeout in milliseconds.",
)
@clean_outputs
def setup(project, uid, identity_file, known_hosts_file, timeout_ms):
    """Prepare SSH access for a sandbox run."""
    try:
        owner, _, project_name, run_uuid = get_project_run_or_local(
            project, uid, is_cli=True
        )
        client = SandboxClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        known_hosts_path = resolve_known_hosts_file(known_hosts_file)
    except PolyaxonClientException as e:
        handle_cli_error(
            e,
            "Could not resolve sandbox run `{}`.".format(uid),
            sys_exit=True,
        )
    try:
        access = prepare_ssh_access(
            client=client,
            identity_file=identity_file,
            timeout_ms=timeout_ms,
        )
        write_known_hosts_entry(
            path=known_hosts_path,
            alias="polyaxon-{}".format(run_uuid),
            host_public_key=access.host_public_key,
        )
    except (ApiException, HTTPError, OSError, PolyaxonClientException) as e:
        handle_cli_error(
            e,
            "Could not prepare SSH access for run `{}`.".format(uid),
            sys_exit=True,
        )
    Printer.success("SSH access prepared.")
    Printer.print("IdentityFile {}".format(access.identity_file))
    Printer.print("UserKnownHostsFile {}".format(known_hosts_path))


@ssh.command("config")
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--identity-file",
    type=click.Path(dir_okay=False),
    help="SSH private key to use. Defaults to Polyaxon's managed sandbox key.",
)
@click.option(
    "--known-hosts-file",
    type=click.Path(dir_okay=False),
    help="Known hosts file to use. Defaults to Polyaxon's managed file.",
)
@clean_outputs
def config_command(project, uid, identity_file, known_hosts_file):
    """Print an SSH config block for a sandbox run."""
    try:
        owner, _, project_name, run_uuid = get_project_run_or_local(
            project, uid, is_cli=True
        )
    except PolyaxonClientException as e:
        handle_cli_error(
            e,
            "Could not resolve sandbox run `{}`.".format(uid),
            sys_exit=True,
        )
    identity_path = resolve_identity_file(identity_file)
    known_hosts_path = resolve_known_hosts_file(known_hosts_file)
    click.echo(
        _ssh_config(
            project_ref="{}/{}".format(owner, project_name),
            run_uuid=run_uuid,
            identity_file=identity_path,
            known_hosts_file=known_hosts_path,
        )
    )


@ssh.command(hidden=True)
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--identity-file",
    type=click.Path(dir_okay=False),
    help="SSH private key to use. Defaults to Polyaxon's managed sandbox key.",
)
@click.option(
    "--known-hosts-file",
    type=click.Path(dir_okay=False),
    help="Known hosts file to use. Defaults to Polyaxon's managed file.",
)
@clean_outputs
def tunnel(project, uid, identity_file, known_hosts_file):
    """Open an SSH tunnel to a sandbox run."""
    with _disable_tunnel_logging():
        try:
            owner, _, project_name, run_uuid = get_project_run_or_local(
                project, uid, is_cli=True
            )
            client = SandboxClient(
                owner=owner,
                project=project_name,
                run_uuid=run_uuid,
                manual_exceptions_handling=True,
            )
            access = prepare_ssh_access(client=client, identity_file=identity_file)
        except (ApiException, HTTPError, PolyaxonClientException) as e:
            _write_tunnel_error("setup", e)
            raise click.exceptions.Exit(1) from e

        try:
            known_hosts_path = resolve_known_hosts_file(known_hosts_file)
            write_known_hosts_entry(
                path=known_hosts_path,
                alias="polyaxon-{}".format(run_uuid),
                host_public_key=access.host_public_key,
            )
        except (OSError, PolyaxonClientException) as e:
            _write_tunnel_error("known_hosts", e)
            raise click.exceptions.Exit(1) from e

        try:
            tunnel_client = SandboxSshTunnelClient(
                url=_ssh_tunnel_url(client),
                headers=_ssh_tunnel_headers(client),
            )
        except (ApiException, HTTPError, PolyaxonClientException) as e:
            _write_tunnel_error("connect", e)
            raise click.exceptions.Exit(1) from e

    code = run_tunnel(
        client=tunnel_client,
        stdin=sys.stdin.buffer,
        stdout=sys.stdout.buffer,
        stderr=sys.stderr,
    )
    if code:
        raise click.exceptions.Exit(code)
