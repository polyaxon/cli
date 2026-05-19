import shlex

import click
from urllib3.exceptions import HTTPError

from clipped.formatting import Printer
from polyaxon._cli.errors import handle_cli_error
from polyaxon._cli.options import OPTIONS_PROJECT, OPTIONS_RUN_UID
from polyaxon._env_vars.getters import get_project_run_or_local
from polyaxon._ssh import prepare_ssh_access, resolve_identity_file
from polyaxon.client import SandboxClient
from polyaxon.exceptions import ApiException, PolyaxonClientException
from polyaxon.logger import clean_outputs


def _sandbox_client(project, uid):
    owner, _, project_name, run_uuid = get_project_run_or_local(project, uid, is_cli=True)
    return SandboxClient(
        owner=owner,
        project=project_name,
        run_uuid=run_uuid,
        manual_exceptions_handling=True,
    )


def _proxy_command(project_ref, run_uuid, identity_file):
    return "polyaxon ssh tunnel -p {} -uid {} --identity-file {}".format(
        shlex.quote(project_ref),
        shlex.quote(run_uuid),
        shlex.quote(str(identity_file)),
    )


def _ssh_config(project_ref, run_uuid, identity_file):
    host = "polyaxon-{}".format(run_uuid)
    return "\n".join(
        [
            "Host {}".format(host),
            "  HostName 127.0.0.1",
            "  User root",
            "  IdentityFile {}".format(identity_file),
            "  StrictHostKeyChecking accept-new",
            "  ProxyCommand {}".format(
                _proxy_command(
                    project_ref=project_ref,
                    run_uuid=run_uuid,
                    identity_file=identity_file,
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
    "--timeout-ms",
    type=click.IntRange(min=1),
    default=30_000,
    show_default=True,
    help="Remote SSH setup timeout in milliseconds.",
)
@clean_outputs
def setup(project, uid, identity_file, timeout_ms):
    """Prepare SSH access for a sandbox run."""
    try:
        client = _sandbox_client(project, uid)
        access = prepare_ssh_access(
            client=client,
            identity_file=identity_file,
            timeout_ms=timeout_ms,
        )
    except (ApiException, HTTPError, PolyaxonClientException) as e:
        handle_cli_error(
            e,
            "Could not prepare SSH access for run `{}`.".format(uid),
            sys_exit=True,
        )
    Printer.success("SSH access prepared.")
    Printer.print("IdentityFile {}".format(access.identity_file))


@ssh.command("config")
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--identity-file",
    type=click.Path(dir_okay=False),
    help="SSH private key to use. Defaults to Polyaxon's managed sandbox key.",
)
@clean_outputs
def config_command(project, uid, identity_file):
    """Print an SSH config block for a sandbox run."""
    try:
        owner, _, project_name, run_uuid = get_project_run_or_local(project, uid, is_cli=True)
    except PolyaxonClientException as e:
        handle_cli_error(
            e,
            "Could not resolve sandbox run `{}`.".format(uid),
            sys_exit=True,
        )
    identity_path = resolve_identity_file(identity_file)
    click.echo(
        _ssh_config(
            project_ref="{}/{}".format(owner, project_name),
            run_uuid=run_uuid,
            identity_file=identity_path,
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
@clean_outputs
def tunnel(project, uid, identity_file):
    """Open an SSH tunnel to a sandbox run."""
    raise click.ClickException("SSH tunnel support is not implemented yet.")
