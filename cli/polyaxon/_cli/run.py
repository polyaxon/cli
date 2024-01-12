import sys

from collections import namedtuple
from typing import Dict, List, Optional

import click

from clipped.formatting import Printer
from clipped.utils import git as git_utils
from clipped.utils.validation import validate_tags
from urllib3.exceptions import HTTPError

from polyaxon._cli.dashboard import get_dashboard_url
from polyaxon._cli.errors import handle_cli_error
from polyaxon._cli.operations import approve
from polyaxon._cli.operations import execute as run_execute
from polyaxon._cli.operations import logs as run_logs
from polyaxon._cli.operations import shell as run_shell
from polyaxon._cli.operations import statuses
from polyaxon._cli.operations import upload as run_upload
from polyaxon._cli.options import OPTIONS_NAME, OPTIONS_PROJECT
from polyaxon._cli.utils import handle_output
from polyaxon._constants.globals import DEFAULT_UPLOADS_PATH
from polyaxon._constants.metadata import META_UPLOAD_ARTIFACTS
from polyaxon._env_vars.getters import get_project_or_local
from polyaxon._flow import V1Operation, V1RunPending
from polyaxon._managers.git import GitConfigManager
from polyaxon._managers.run import RunConfigManager
from polyaxon._polyaxonfile import check_polyaxonfile
from polyaxon._runner.kinds import RunnerKind
from polyaxon._schemas.lifecycle import ManagedBy
from polyaxon._utils import cache
from polyaxon.client import RunClient
from polyaxon.exceptions import ApiException
from polyaxon.logger import clean_outputs


class RunWatchSpec(namedtuple("RunWatchSpec", "uuid name")):
    pass


def _run(
    ctx,
    name: str,
    owner: str,
    project_name: str,
    description: str,
    tags: List[str],
    op_spec: V1Operation,
    log: bool,
    shell: bool,
    upload: bool,
    upload_to: str,
    upload_from: str,
    watch: bool,
    output: Optional[str] = None,
    local: Optional[bool] = False,
    executor: Optional[RunnerKind] = None,
):
    polyaxon_client = RunClient(
        owner=owner, project=project_name, manual_exceptions_handling=True
    )

    def get_instance_info(r):
        rn = (
            f"[white]{r.name}[/white]@[white]{r.uuid}[/white]"
            if r.name
            else "[white]{r.uuid}[/white]"
        )
        return f"[white]{owner}[/white]/[white]{project_name}[/white]:{rn}"

    def cache_run(data):
        config = polyaxon_client.client.sanitize_for_serialization(data)
        cache.cache(
            config_manager=RunConfigManager,
            config=config,
            owner=owner,
            project=project_name,
        )

    def create_run(
        managed_by: Optional[ManagedBy] = ManagedBy.AGENT,
        meta_info: Optional[Dict] = None,
        pending: Optional[str] = None,
    ):
        try:
            response = polyaxon_client.create(
                name=name,
                description=description,
                tags=tags,
                content=op_spec,
                managed_by=managed_by,
                meta_info=meta_info,
                pending=pending,
            )
            run_url = get_dashboard_url(
                subpath="{}/{}/runs/{}".format(owner, project_name, response.uuid)
            )
            if output:
                response_data = polyaxon_client.client.sanitize_for_serialization(
                    response
                )
                response_data["url"] = run_url
                handle_output(response_data, output)
                return
            Printer.success(
                "A new run was created: {}".format(get_instance_info(response))
            )

            cache_run(response)
            Printer.print("You can view this run on Polyaxon UI: {}".format(run_url))

            return response
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e,
                message="Could not create a run.",
                http_messages_mapping={
                    404: "Make sure you have a project initialized in your current workdir, "
                    "otherwise you need to pass a project with `-p/--project`. "
                    "The project {}/{} does not exist.".format(owner, project_name)
                },
            )
            sys.exit(1)

    def execute_run_locally(run_uuid: str):
        ctx.obj = {
            "project": "{}/{}".format(owner, project_name),
            "run_uuid": run_uuid,
            "executor": executor,
        }
        ctx.invoke(run_execute)

    def watch_run_statuses(run_uuid: str):
        ctx.obj = {"project": "{}/{}".format(owner, project_name), "run_uuid": run_uuid}
        ctx.invoke(statuses, watch=True)

    def watch_run_logs(run_uuid: str):
        ctx.obj = {"project": "{}/{}".format(owner, project_name), "run_uuid": run_uuid}
        ctx.invoke(run_logs)

    def start_run_shell(run_uuid: str):
        ctx.obj = {"project": "{}/{}".format(owner, project_name), "run_uuid": run_uuid}
        ctx.invoke(run_shell)

    def upload_run(run_uuid: str):
        ctx.obj = {"project": "{}/{}".format(owner, project_name), "run_uuid": run_uuid}
        ctx.invoke(
            run_upload, path_to=upload_to, path_from=upload_from, sync_failure=True
        )
        ctx.invoke(approve)

    if not output:
        Printer.print("Creating a new run...")
    managed_by = ManagedBy.AGENT
    run_meta_info = None
    if local:
        managed_by = ManagedBy.CLI
    if upload:
        upload_to = upload_to or DEFAULT_UPLOADS_PATH
        run_meta_info = run_meta_info or {}
        run_meta_info[META_UPLOAD_ARTIFACTS] = upload_to
    run_instance = create_run(
        managed_by=managed_by,
        meta_info=run_meta_info,
        pending=V1RunPending.UPLOAD if upload else None,
    )
    if not run_instance:
        return

    runs_to_watch = [RunWatchSpec(run_instance.uuid, run_instance.name)]

    build_uuid = None
    if run_instance.pending == V1RunPending.BUILD and run_instance.settings.build:
        build_uuid = run_instance.settings.build.get("uuid")
        build_name = run_instance.settings.build.get("name")
        runs_to_watch.insert(0, RunWatchSpec(build_uuid, build_name))

    if upload:
        upload_run(build_uuid or run_instance.uuid)

    if local:
        for instance in runs_to_watch:
            execute_run_locally(instance.uuid)

    # Check if we need to invoke logs
    if watch:
        for instance in runs_to_watch:
            Printer.header(f"Starting watch for run: {get_instance_info(instance)}")
            watch_run_statuses(instance.uuid)
    if log:
        for instance in runs_to_watch:
            Printer.header(f"Starting logs for run: {get_instance_info(instance)}")
            watch_run_logs(instance.uuid)
    if shell:
        for instance in runs_to_watch:
            Printer.header(
                f"Starting shell session for run: {get_instance_info(instance)}",
            )
            start_run_shell(instance.uuid)


@click.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(
    "-f",
    "--file",
    "polyaxonfile",
    multiple=True,
    type=click.Path(exists=True),
    help="The polyaxonfiles to run.",
)
@click.option(
    "-pm",
    "--python-module",
    type=str,
    help="The python module containing the polyaxonfile to run.",
)
@click.option(
    "--url",
    type=str,
    help="The url containing the polyaxonfile to run.",
)
@click.option(
    "--hub",
    type=str,
    help="The Component Hub name containing the polyaxonfile to run.",
)
@click.option(
    *OPTIONS_NAME["args"],
    type=str,
    help="Name to give to this run, must be unique within the project, could be none.",
)
@click.option("--tags", type=str, help="Tags of this run (comma separated values).")
@click.option("--description", type=str, help="The description to give to this run.")
@click.option(
    "--shell",
    "-s",
    is_flag=True,
    default=False,
    help="To start a shell session after scheduling the run.",
)
@click.option(
    "--log",
    "--logs",
    "-l",
    is_flag=True,
    default=False,
    help="To start logging after scheduling the run.",
)
@click.option(
    "--upload",
    "-u",
    is_flag=True,
    default=False,
    help="To upload the working dir to run's artifacts path "
    "as an init context before scheduling the run.",
)
@click.option(
    "--upload-from",
    "-u-from",
    type=str,
    help="The path to upload from relative the current location (or absolute path), "
    "Note that this must be a valid path, or the CLI will raise an error. "
    "Defaults to the current path.",
)
@click.option(
    "--upload-to",
    "-u-to",
    type=str,
    help="The path to upload to relative the run's root context."
    "To upload to root path you can use `/`, "
    "otherwise the values should start without the separator, "
    "e.g. `uploads`, `code`, `dataset/images/values`, ...",
)
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    default=False,
    help="To start statuses watch loop after scheduling the run.",
)
@click.option(
    "--local",
    is_flag=True,
    default=False,
    help="To start the run locally, with `docker` environment as default.",
)
@click.option(
    "--executor",
    "-exc",
    type=str,
    help="The local executor to use, possible values are: docker, k8s, process.",
)
@click.option(
    "--params",
    "--param",
    "-P",
    metavar="NAME=VALUE",
    multiple=True,
    help="A parameter to override the default params of the run, "
    "form `-P name=value` or `--param name=value`.",
)
@click.option(
    "--hparams",
    "--hparam",
    "-HP",
    metavar="NAME=VALUE",
    multiple=True,
    help="A hyper-parameter to override the default params of the run, "
    "form: -HP name='range:start:stop:step' "
    "or -HP name='range:[start,stop,step]' "
    "or -HP name='choice:[v1,v2,v3,...]'",
)
@click.option(
    "--matrix-kind", type=str, help="Matrix kind if hparams are provided, default grid."
)
@click.option(
    "--matrix-concurrency",
    type=int,
    help="Matrix concurrency if hparams are provided, default 1.",
)
@click.option(
    "--matrix-num-runs",
    type=int,
    help="Matrix maximum number of runs to create, default all.",
)
@click.option("--presets", type=str, help="Name of the presets to use for this run.")
@click.option(
    "--queue",
    "-q",
    type=str,
    help="Name of the queue to use for this run. "
    "If the name is not namespaced by the agent name the default agent is used: "
    "queue-name or agent-name/queue-name",
)
@click.option(
    "--namespace",
    "-ns",
    type=str,
    help="Namespace to use for this run. By default it will use the agent's namespace.",
)
@click.option(
    "--nocache",
    is_flag=True,
    default=False,
    help="[DEPRECATED] Please use '--cache=f' instead. "
    "Disable cache check before starting this operation.",
)
@click.option(
    "--cache",
    help="To enable/disable cache check before starting this operation, "
    "similar to 'cache: {disable: true/false}'. "
    "Can be used with yes/no, y/n, false/true, f/t, 1/0. "
    "e.g. '--cache=1', '--cache=yes', '--cache=false', '--cache=t', ...",
)
@click.option(
    "--approved",
    help="To enable/disable human in the loop validation without changing the polyaxonfile, "
    "similar to 'isApproved: true/false'. "
    "Can be used with yes/no, y/n, false/true, f/t, 1/0. "
    "e.g. '--approved=1', '--approved=yes', '--approved=false', '--approved=t', ...",
)
@click.option(
    "--git-preset",
    is_flag=True,
    default=False,
    help="A flag to enable automatic injection of a git initializer as a preset "
    "using the initialized git connection.",
)
@click.option(
    "--git-revision",
    type=str,
    help="If provided, Polyaxon will use this git revision "
    "instead of trying to detected and use the latest commit. "
    "The git revision could be a commit or a branch or any valid tree-ish. "
    "This flag is only used when the repo is initialized with: "
    "`polyaxon init [--git-connection] [--git-url]`",
)
@click.option(
    "--ignore-template",
    is_flag=True,
    default=False,
    help="If provided, Polyaxon will ignore template definition and "
    "submit the manifest to be checked by the API.",
)
@click.option(
    "--output",
    "-o",
    type=str,
    help="Optional flag to print the response as a json object or store the response as json file."
    "Example `-o json` or `-o path=./data.json`",
)
@click.pass_context
@clean_outputs
def run(
    ctx,
    project,
    polyaxonfile,
    python_module,
    url,
    hub,
    name,
    tags,
    description,
    shell,
    log,
    upload,
    upload_from,
    upload_to,
    watch,
    local,
    executor,
    params,
    hparams,
    matrix_kind,
    matrix_concurrency,
    matrix_num_runs,
    presets,
    queue,
    namespace,
    nocache,
    cache,
    approved,
    git_preset,
    git_revision,
    ignore_template,
    output,
):
    """Run polyaxonfile specification.

    Examples:

    \b
    $ polyaxon run -f file -f file_override ...

    Run and set description and tags for this run

    \b
    $ polyaxon run -f file --description="Description of the current run" --tags="foo, bar, moo"

    Run and set a unique name for this run

    \b
    polyaxon run --name=foo

    Run for a specific project

    \b
    $ polyaxon run -p project1 -f file.yaml

    Run with updated params

    \b
    $ polyaxon run -p project1 -f file.yaml -P param1=234.2 -P param2=relu

    If a python file contains a component main, you can run that component

    \b
    $ polyaxon run -pm path/to/my-component.py


    If a python file contains more than one component, you can specify the component to run

    \b
    $ polyaxon run -pm path/to/my-component.py:componentA


    Uploading from everything in the current folder to the default uploads path

    \b
    $ polyaxon run ... -u


    Uploading from everything in the current folder to a custom path, e.g. code

    \b
    $ polyaxon run ... -u-to code

    Uploading from everything from a sub-folder, e.g. ./code to the a custom path, e.g. new-code

    \b
    $ polyaxon run ... -u-from ./code -u-to new-code
    """
    if log and shell:
        Printer.error(
            "You can't use `--logs` and `--shell` at the same, please keep one option.",
            sys_exit=True,
        )
    if cache and nocache:
        Printer.error(
            "You can't use `--cache` and `--nocache` at the same.", sys_exit=True
        )
    if nocache:
        Printer.error(
            "'--nocache' is DEPRECATED and will be removed in the future, "
            "please use '--cache=f' instead.",
        )
    if (upload_to or upload_from) and not upload:
        upload = True

    git_init = None
    if git_preset or git_revision:
        # Check that the current path was initialized
        if not GitConfigManager.is_initialized():
            Printer.error(
                "You can't use `--git-preset [--git-revision]`, "
                "the current path is not initialized with a valid git connection or a git url, "
                "please run `polyaxon init [--git-connection] [--git-url]` "
                "to set a valid git configuration.",
                sys_exit=True,
            )
        git_init = GitConfigManager.get_config()
        if git_revision:
            git_init.git.revision = git_revision
        elif git_utils.is_git_initialized(path="."):
            if git_utils.is_dirty(path="."):
                Printer.warning(
                    "Polyaxon detected uncommitted changes in the current git repo!"
                )
            commit_hash = git_utils.get_commit()
            git_init.git.revision = commit_hash
        else:
            Printer.warning(
                "Polyaxon could not find a valid git repo, "
                "and will not add the current commit to the git initializer."
            )

    presets = validate_tags(presets)

    op_spec = check_polyaxonfile(
        polyaxonfile=polyaxonfile,
        python_module=python_module,
        url=url,
        hub=hub,
        params=params,
        hparams=hparams,
        matrix_kind=matrix_kind,
        matrix_concurrency=matrix_concurrency,
        matrix_num_runs=matrix_num_runs,
        presets=presets,
        queue=queue,
        namespace=namespace,
        cache=cache,
        nocache=nocache,
        approved=approved,
        verbose=False,
        git_init=git_init,
        ignore_template=ignore_template,
    )

    if ignore_template:
        op_spec.disable_template()
    if op_spec.is_template():
        Printer.print("Please customize the specification or disable the template!")
        sys.exit(1)

    owner, project_name = get_project_or_local(project, is_cli=True)
    tags = validate_tags(tags, validate_yaml=True)

    _run(
        ctx=ctx,
        name=name,
        owner=owner,
        project_name=project_name,
        description=description,
        tags=tags,
        op_spec=op_spec,
        log=log,
        upload=upload,
        upload_to=upload_to,
        upload_from=upload_from,
        watch=watch,
        output=output,
        shell=shell,
        local=local,
        executor=executor,
    )
