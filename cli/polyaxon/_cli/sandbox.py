import shlex
import shutil
import sys

import click
from urllib3.exceptions import HTTPError

from clipped.formatting import Printer
from polyaxon._cli.errors import handle_cli_error
from polyaxon._cli.options import OPTIONS_PROJECT, OPTIONS_RUN_UID
from polyaxon._cli.utils import CommandSeparatorCommand
from polyaxon._env_vars.getters import get_project_run_or_local
from polyaxon._pty.sandbox import SandboxPseudoTerminal
from polyaxon._sandbox.client_utils import validate_remote_path
from polyaxon.client import SandboxClient
from polyaxon.exceptions import ApiException, PolyaxonClientException
from polyaxon.logger import clean_outputs


def _sandbox_client(project, uid):
    owner, _, project_name, run_uuid = get_project_run_or_local(
        project,
        uid,
        is_cli=True,
    )
    return SandboxClient(
        owner=owner,
        project=project_name,
        run_uuid=run_uuid,
        manual_exceptions_handling=True,
    )


def _write(data, err: bool = False):
    if not data:
        return
    stream = sys.stderr if err else sys.stdout
    stream.write(data)
    stream.flush()


def _event_data(event):
    return event.get("text") or event.get("data") or ""


def _remote_exit_code(value):
    return 1 if value is None else int(value)


def _terminal_size(cols, rows):
    if cols and rows:
        return cols, rows
    size = shutil.get_terminal_size(fallback=(80, 24))
    return cols or size.columns, rows or size.lines


def _shell_command(command: str):
    if command is None:
        command = "sh"
    value = shlex.split(command)
    if not value:
        raise click.ClickException("shell command must not be empty")
    return value


def _validate_remote_file_path(path: str):
    if not path:
        raise click.ClickException("remote path is empty")
    if path.endswith("/"):
        raise click.ClickException("remote path must include filename")
    try:
        path = validate_remote_path(path)
    except (TypeError, ValueError) as e:
        raise click.ClickException(str(e)) from e
    return path


@click.group()
@clean_outputs
def sandbox():
    """Commands for sandbox-enabled runs."""


@sandbox.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@clean_outputs
def ping(project, uid):
    """Check sandbox health."""
    try:
        client = _sandbox_client(project, uid)
        response = client.ping()
    except (ApiException, HTTPError, PolyaxonClientException) as e:
        handle_cli_error(
            e,
            "Could not ping sandbox run `{}`.".format(uid),
            sys_exit=True,
        )
    Printer.print(response.status)
    if getattr(response, "version", None):
        Printer.print(response.version)


@sandbox.command("exec", cls=CommandSeparatorCommand)
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option("--stream", is_flag=True, default=False, help="Stream command output.")
@click.option("--detach", is_flag=True, default=False, help="Start command and exit.")
@click.option("--tag", type=str, help="Optional tag for detached commands.")
@click.option("--timeout-ms", type=int, help="Remote command timeout in milliseconds.")
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
@clean_outputs
def exec_command(ctx, project, uid, stream, detach, tag, timeout_ms, command):
    """Execute a command in a sandbox run.

    The command must follow a `--` separator:

    \b
    $ polyaxon sandbox exec -p owner/project -uid UUID -- python -V
    """
    if stream and detach:
        raise click.UsageError("Use only one of --stream or --detach.")

    try:
        client = _sandbox_client(project, uid)
        if detach:
            bg = client.process.exec_bg(
                command=command,
                timeout_ms=timeout_ms,
                tag=tag,
            )
            Printer.print(bg.id)
            return

        if stream:
            exit_code = None
            with client.process.exec_stream(
                command=command,
                timeout_ms=timeout_ms,
            ) as events:
                for event in events:
                    event_type = event.get("type")
                    if event_type == "stdout":
                        _write(_event_data(event))
                    elif event_type == "stderr":
                        _write(_event_data(event), err=True)
                    elif event_type == "error":
                        _write(_event_data(event) or str(event), err=True)
                        ctx.exit(1)
                    elif event_type == "execution_complete":
                        exit_code = _remote_exit_code(event.get("exit_code"))
                        break
            if exit_code is None:
                raise click.ClickException("stream ended without completion event")
            ctx.exit(exit_code)

        result = client.process.exec(command=command, timeout_ms=timeout_ms)
        _write(getattr(result, "stdout", None))
        _write(getattr(result, "stderr", None), err=True)
        ctx.exit(_remote_exit_code(getattr(result, "exit_code", None)))
    except (ApiException, HTTPError, PolyaxonClientException) as e:
        handle_cli_error(
            e,
            "Could not execute sandbox command for run `{}`.".format(uid),
            sys_exit=True,
        )


@sandbox.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--stream",
    "stream",
    type=click.Choice(["stdout", "stderr"]),
    default="stdout",
    show_default=True,
    help="The background log stream.",
)
@click.option("--offset", type=int, default=0, show_default=True, help="Log offset.")
@click.option("--max-bytes", type=int, help="Maximum bytes to read.")
@click.argument("exec_id")
@clean_outputs
def logs(project, uid, stream, offset, max_bytes, exec_id):
    """Read background exec logs."""
    try:
        client = _sandbox_client(project, uid)
        response = client.process.logs(
            exec_id,
            stream=stream,
            offset=offset,
            max_bytes=max_bytes,
        )
    except (ApiException, HTTPError, PolyaxonClientException) as e:
        handle_cli_error(
            e, "Could not read sandbox logs for run `{}`.".format(uid), sys_exit=True
        )
    _write(getattr(response, "data", None) or "")


@sandbox.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option("--recursive", is_flag=True, default=False, help="List recursively.")
@click.option("--max-entries", type=int, help="Maximum entries to return.")
@click.argument("path")
@clean_outputs
def ls(project, uid, recursive, max_entries, path):
    """List a sandbox directory."""
    try:
        client = _sandbox_client(project, uid)
        response = client.fs.ls(
            path,
            recursive=recursive,
            max_entries=max_entries,
        )
    except (ApiException, HTTPError, PolyaxonClientException, ValueError) as e:
        handle_cli_error(
            e, "Could not list sandbox path `{}`.".format(path), sys_exit=True
        )

    for entry in getattr(response, "entries", None) or []:
        Printer.print(
            "{}\t{}\t{}\t{}".format(
                getattr(entry, "type", "") or "",
                getattr(entry, "mode", "") or "",
                getattr(entry, "size", "") or "",
                getattr(entry, "name", "") or "",
            )
        )


@sandbox.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--chunk-size",
    type=click.IntRange(min=1),
    default=64 * 1024,
    show_default=True,
)
@click.argument("path_from")
@click.argument("path_to")
@clean_outputs
def upload(project, uid, chunk_size, path_from, path_to):
    """Upload one local file to a sandbox run."""
    path_to = _validate_remote_file_path(path_to)
    try:
        client = _sandbox_client(project, uid)
        client.fs.upload_file(
            local_path=path_from,
            path=path_to,
            chunk_size=chunk_size,
        )
        Printer.success("Uploaded `{}` to `{}`.".format(path_from, path_to))
    except (ApiException, HTTPError, PolyaxonClientException, ValueError) as e:
        handle_cli_error(e, "Could not upload sandbox file.", sys_exit=True)


@sandbox.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--chunk-size",
    type=click.IntRange(min=1),
    default=64 * 1024,
    show_default=True,
)
@click.argument("path_from")
@click.argument("path_to")
@clean_outputs
def download(project, uid, chunk_size, path_from, path_to):
    """Download one sandbox file to a local path."""
    path_from = _validate_remote_file_path(path_from)
    try:
        client = _sandbox_client(project, uid)
        client.fs.download_file(
            path=path_from,
            local_path=path_to,
            chunk_size=chunk_size,
        )
        Printer.success("Downloaded `{}` to `{}`.".format(path_from, path_to))
    except (ApiException, HTTPError, PolyaxonClientException, ValueError) as e:
        handle_cli_error(e, "Could not download sandbox file.", sys_exit=True)


@sandbox.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--command",
    "-cmd",
    type=str,
    default="sh",
    show_default=True,
    help="The shell command to start.",
)
@click.option("--cols", type=click.IntRange(min=1), help="Initial terminal columns.")
@click.option("--rows", type=click.IntRange(min=1), help="Initial terminal rows.")
@click.option(
    "--replay-bytes",
    type=click.IntRange(min=0),
    default=0,
    show_default=True,
    help="PTY output bytes to replay on attach.",
)
@clean_outputs
def shell(project, uid, command, cols, rows, replay_bytes):
    """Start an interactive shell in a sandbox run."""
    try:
        client = _sandbox_client(project, uid)
        cols, rows = _terminal_size(cols=cols, rows=rows)
        pty = client.pty.create(
            command=_shell_command(command),
            cols=cols,
            rows=rows,
        )
        ws = client.pty.attach(pty.pty_id, replay_bytes=replay_bytes)
        exit_code = SandboxPseudoTerminal(ws).start()
    except (ApiException, HTTPError, PolyaxonClientException) as e:
        handle_cli_error(e, "Could not start sandbox shell.", sys_exit=True)
    raise click.exceptions.Exit(exit_code)
