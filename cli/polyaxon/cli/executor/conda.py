import os
import subprocess
import sys

from clipped.formatting import Printer
from clipped.utils.hashing import hash_value

from polyaxon.cli.errors import handle_cli_error
from polyaxon.deploy.operators.conda import CondaOperator
from polyaxon.exceptions import (
    PolyaxonClientException,
    PolyaxonException,
    PolyaxonHTTPError,
    PolyaxonShouldExitError,
)


def _get_conda_env_name(conda_env):
    conda_env_contents = open(conda_env).read() if conda_env else ""
    conda_tag = hash_value(conda_env_contents)
    return "polyaxon-{}".format(conda_tag)


def _run(
    ctx, name, owner, project_name, description, tags, specification, log, conda_env
):
    conda = CondaOperator()
    # cmd = CmdOperator()
    if not conda.check():
        raise PolyaxonException("Conda is required to run this command.")

    envs = conda.execute(["env", "list", "--json"], is_json=True)
    env_names = [os.path.basename(env) for env in envs["envs"]]
    project_env_name = _get_conda_env_name(conda_env)
    if project_env_name not in env_names:
        Printer.info("Creating conda environment {}".format(project_env_name))
        conda.execute(
            ["env", "create", "-n", project_env_name, "--file", conda_env], stream=True
        )

    cmd_bash, cmd_args = specification.run.get_container_cmd()
    cmd_args = ["source activate {}".format(project_env_name)] + cmd_args
    subprocess.Popen(cmd_bash + [" && ".join(cmd_args)], close_fds=True)


def run(
    ctx, name, owner, project_name, description, tags, specification, log, conda_env
):
    try:
        _run(
            ctx,
            name,
            owner,
            project_name,
            description,
            tags,
            specification,
            log,
            conda_env,
        )
    except (PolyaxonHTTPError, PolyaxonShouldExitError, PolyaxonClientException) as e:
        handle_cli_error(e, message="Could start local run.")
        sys.exit(1)
    except Exception as e:
        Printer.error("Could not start local run.")
        Printer.error("Unexpected Error: `{}`.".format(e))
        sys.exit(1)
