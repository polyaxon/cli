import os
import subprocess

from typing import List, Optional

from clipped.formatting import Printer

from polyaxon._init.artifacts import download_artifact
from polyaxon.client import RunClient


def _download(
    connection_name: str,
    connection_kind: str,
    context_from: str,
    context_to: str,
    path_from: str,
    path_to: str,
):
    download_artifact(
        connection_name=connection_name,
        connection_kind=connection_kind,
        path_to=os.path.join(context_to, path_to),
        path_from=os.path.join(context_from, path_from, "outputs/tensorboard"),
        is_file=False,
        raise_errors=False,
        sync_fw=False,
        check_path=False,
    )


def _command(
    script_path: str,
    port: int,
    logdir: str,
    path_prefix: str,
    plugins: Optional[List[str]] = None,
):
    cmd = []

    if plugins:
        cmd.append("pip install {}".format(" ".join(plugins)))

    cmd.append(
        f"tensorboard  --logdir={logdir} --port={port} --path_prefix={path_prefix} --host=0.0.0.0"
    )

    with open(script_path, "w") as script:
        script.write(" && ".join(cmd))
        subprocess.check_call(["chmod", "+x", script_path])
    Printer.success("Tensorboard script is initialized, path: `{}`".format(script_path))


def initialize_tensorboard(
    port: int,
    connection_name: str,
    connection_kind: str,
    context_from: str,
    context_to: str,
    uuids: List[str],
    use_names: bool,
    path_prefix: str,
    plugins: List[str],
):
    tensorboard_context = os.path.join(context_to, "tensorboard")
    if use_names:
        used_names = set([])
        for op in RunClient().list(query="uuid:{}".format("|".join(uuids))).results:
            op_name = op.name
            if op_name in used_names:
                op_name = f"{op.name}-{op.uuid[:10]}"
            else:
                used_names.add(op.name)
            _download(
                connection_name=connection_name,
                connection_kind=connection_kind,
                context_to=tensorboard_context,
                context_from=context_from,
                path_from=op.uuid,
                path_to=op_name,
            )
    else:
        for op in uuids:
            _download(
                connection_name=connection_name,
                connection_kind=connection_kind,
                context_to=tensorboard_context,
                context_from=context_from,
                path_from=op,
                path_to=op,
            )

    script_path = os.path.join(context_to, "start_tensorboard")
    _command(
        script_path=script_path,
        port=port,
        logdir=tensorboard_context,
        path_prefix=path_prefix,
        plugins=plugins,
    )
