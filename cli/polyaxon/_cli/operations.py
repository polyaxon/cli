import os
import sys

from typing import Any

import click

from clipped.formatting import Printer
from clipped.utils.csv import write_csv
from clipped.utils.dicts import (
    dict_to_tabulate,
    flatten_keys,
    list_dicts_to_csv,
    list_dicts_to_tabulate,
)
from clipped.utils.json import orjson_dumps
from clipped.utils.lists import to_list
from clipped.utils.responses import get_meta_response
from clipped.utils.validation import validate_tags
from clipped.utils.versions import compare_versions
from urllib3.exceptions import HTTPError

from polyaxon import settings
from polyaxon._cli.dashboard import get_dashboard, get_dashboard_url
from polyaxon._cli.errors import handle_cli_error, is_in_ce
from polyaxon._cli.options import (
    OPTIONS_NAME,
    OPTIONS_PROJECT,
    OPTIONS_RUN_OFFLINE,
    OPTIONS_RUN_OFFLINE_PATH_FROM,
    OPTIONS_RUN_OFFLINE_PATH_TO,
    OPTIONS_RUN_UID,
)
from polyaxon._cli.utils import handle_output
from polyaxon._constants.metadata import META_IS_EXTERNAL, META_PORTS, META_REWRITE_PATH
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.getters import get_project_or_local, get_project_run_or_local
from polyaxon._flow import V1RunKind
from polyaxon._managers.run import RunConfigManager
from polyaxon._polyaxonfile import OperationSpecification
from polyaxon._runner.kinds import RunnerKind
from polyaxon._schemas.lifecycle import LifeCycle, V1ProjectFeature, V1Statuses
from polyaxon._utils import cache
from polyaxon.api import (
    EXTERNAL_V1,
    REWRITE_EXTERNAL_V1,
    REWRITE_SERVICES_V1,
    SERVICES_V1,
)
from polyaxon.client import RunClient, V1Run, get_run_logs
from polyaxon.exceptions import (
    ApiException,
    PolyaxonClientException,
    PolyaxonHTTPError,
    PolyaxonShouldExitError,
)
from polyaxon.logger import clean_outputs

DEFAULT_EXCLUDE = [
    "owner",
    "project",
    "description",
    "content",
    "raw_content",
    "live_state",
    "readme",
    "bookmarked",
    "settings",
    "meta_info",
    "is_approved",
    "is_managed",
    "managed_by",
    "schedule_at",
    "original",
    "pipeline",
    "role",
    "status_conditions",
    "graph",
    "resources",
    "merge",
    "pending",
]


def handle_run_statuses(status, conditions, table):
    if not conditions:
        return False

    Printer.print(
        "Latest status: {}".format(
            Printer.add_status_color({"status": status}, status_key="status")["status"]
        )
    )

    def get_condition(c):
        if hasattr(c, "to_dict"):
            c = c.to_dict()
        return dict_to_tabulate(
            Printer.add_status_color(c, status_key="type"), timesince=False
        )

    objects = [get_condition(c) for c in conditions]

    if not objects:
        return False

    if not table.columns:
        for c in objects[0].keys():
            table.add_column(c)
    if objects:
        for o in objects:
            table.add_row(*o.values())

    return True


def get_run_details(run):  # pylint:disable=redefined-outer-name
    if run.description:
        Printer.heading("Run description:")
        Printer.print_text("{}\n".format(run.description))

    if run.inputs:
        Printer.heading("Run inputs:")
        Printer.dict_tabulate(run.inputs)

    if run.outputs:
        Printer.heading("Run outputs:")
        Printer.dict_tabulate(run.outputs)

    if run.settings:
        Printer.heading("Run settings:")
        Printer.dict_tabulate(
            run.settings.to_dict() if hasattr(run.settings, "to_dict") else run.settings
        )

    if run.meta_info:
        Printer.heading("Run meta info:")
        Printer.dict_tabulate(run.meta_info)

    if run.readme:
        Printer.heading("Run readme:")
        Printer.print_md(run.readme)

    response = Printer.add_status_color(run.to_dict())
    response = dict_to_tabulate(
        response,
        humanize_values=True,
        exclude_attrs=[
            "description",
            "readme",
            "content",
            "raw_content",
            "inputs",
            "outputs",
            "managed_by",
            "is_managed",
            "status_conditions",
            "settings",
            "meta_info",
            "graph",
            "merge",
        ],
    )

    Printer.heading("Run info:")
    Printer.dict_tabulate(response)


@click.group()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.pass_context
@clean_outputs
def ops(ctx, project, uid):
    """Commands for ops/runs."""
    ctx.obj = ctx.obj or {}
    if project or uid:
        Printer.warning(
            "Passing arguments to command groups is deprecated and will be removed in v2! "
            "Please use arguments on the sub-command directly: `polyaxon ops SUB_COMMAND --help`"
        )
    ctx.obj["project"] = project
    if ctx.invoked_subcommand not in ["ls"]:
        ctx.obj["run_uuid"] = uid


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(
    "--io",
    "-io",
    is_flag=True,
    help="List runs with their inputs/outputs (params, metrics, results, ...).",
)
@click.option(
    "--to-csv",
    is_flag=True,
    help="Saves the results to a csv file. Note that this flag requires pandas",
)
@click.option(
    "--query", "-q", type=str, help="To filter the runs based on a query spec."
)
@click.option(
    "--sort", "-s", type=str, help="To order the runs based on this sort spec."
)
@click.option("--limit", "-l", type=int, help="To limit the list of runs.")
@click.option("--offset", "-off", type=int, help="To offset the list of runs.")
@click.option("--columns", "-c", type=str, help="The columns to show.")
@click.option(*OPTIONS_RUN_OFFLINE["args"], **OPTIONS_RUN_OFFLINE["kwargs"])
@click.option(
    *OPTIONS_RUN_OFFLINE_PATH_FROM["args"], **OPTIONS_RUN_OFFLINE_PATH_FROM["kwargs"]
)
@click.option(
    "--output",
    "-o",
    type=str,
    help="Optional flag to print the results as a json object or store the results as json file"
    "Example `-o json` or `-o path=./data.json`",
)
@click.pass_context
@clean_outputs
def ls(
    ctx,
    project,
    io,
    to_csv,
    query,
    sort,
    limit,
    offset,
    columns,
    offline,
    path,
    output,
):
    """List runs for this project.

    Uses /docs/core/cli/#caching

    Examples:

    Get all runs:

    \b

    Get all runs with status {created or running}, and
    creation date between 2018-01-01 and 2018-01-02, and params activation equal to sigmoid
    and metric loss less or equal to 0.2

    \b
    $ polyaxon ops ls \
    -q "status:created|running, started_at:2018-01-01..2018-01-02, \
    params.activation:sigmoid, metrics.loss:<=0.2"


    Get all runs sorted by update date:

    \b
    $ polyaxon ops ls -s "-updated_at"

    Get all runs of kind job:

    \b
    $ polyaxon ops ls -q "kind: job"

    Get all runs of kind service:

    \b
    $ polyaxon ops ls -q "kind: service"
    """
    if offline:
        offline_path = ctx_paths.get_offline_base_path(
            entity_kind=V1ProjectFeature.RUNTIME, path=path
        )
        if not os.path.exists(offline_path) or not os.path.isdir(offline_path):
            Printer.error(
                f"Could not list offline runs, the path `{offline_path}` "
                f"does not exist or is not a directory."
            )
            sys.exit(1)
        results = []
        for uid in os.listdir(offline_path):
            run_path = "{}/{}/{}".format(offline_path, uid, ctx_paths.CONTEXT_LOCAL_RUN)
            if os.path.exists(run_path):
                results.append(RunConfigManager.read_from_path(run_path))
            else:
                Printer.warning(f"Skipping run {uid}, offline data not found.")
    else:
        owner, project_name = get_project_or_local(
            project or ctx.obj.get("project"), is_cli=True
        )

        try:
            polyaxon_client = RunClient(
                owner=owner, project=project_name, manual_exceptions_handling=True
            )
            response = polyaxon_client.list(
                limit=limit, offset=offset, query=query, sort=sort
            )
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e, message="Could not get runs for project `{}`.".format(project_name)
            )
            sys.exit(1)

        if output:
            config = polyaxon_client.client.sanitize_for_serialization(response)
            handle_output(config, output)
            return
        meta = get_meta_response(response)
        if meta:
            Printer.heading("Runs for project `{}/{}`.".format(owner, project_name))
            Printer.heading("Navigation:")
            Printer.dict_tabulate(meta)
        else:
            Printer.heading(
                "No runs found for project `{}/{}`.".format(owner, project_name)
            )

        results = response.results

    objects = [o.to_dict() for o in results]
    if not to_csv:
        objects = [Printer.add_status_color(o) for o in objects]
    columns = validate_tags(columns, validate_yaml=True)
    if io:
        objects, prefixed_columns = flatten_keys(
            objects=objects,
            columns=["inputs", "outputs"],
            columns_prefix={"inputs": "in", "outputs": "out"},
        )
        if columns:
            columns = {prefixed_columns.get(col, col) for col in columns}
        if to_csv:
            objects = list_dicts_to_csv(
                objects,
                include_attrs=columns,
                exclude_attrs=DEFAULT_EXCLUDE,
            )
        else:
            objects = list_dicts_to_tabulate(
                objects,
                include_attrs=columns,
                exclude_attrs=DEFAULT_EXCLUDE,
                humanize_values=True,
                upper_keys=False,
            )
    else:
        if to_csv:
            objects = list_dicts_to_csv(
                objects,
                include_attrs=columns,
                exclude_attrs=DEFAULT_EXCLUDE + ["inputs", "outputs"],
            )
        else:
            objects = list_dicts_to_tabulate(
                objects,
                include_attrs=columns,
                exclude_attrs=DEFAULT_EXCLUDE + ["inputs", "outputs"],
                humanize_values=True,
                upper_keys=False,
            )
    if objects:
        if to_csv:
            filename = "./results.csv"
            write_csv(objects, filename=filename)
            Printer.success("CSV file generated: `{}`".format(filename))
        else:
            for o in objects:
                o.pop("project_name", None)
            all_columns = objects[0].keys()
            Printer.heading("Displayed columns ({}):".format(len(all_columns)))
            Printer.print(" | ".join(all_columns))
            Printer.info("\nTips:")
            Printer.tip("  1. You can enable the inputs/outputs columns using `-io`")
            Printer.tip(
                "  2. You can select the columns to show using `-c col1,cl2,col3,...`"
            )
            Printer.heading("Runs:")
            Printer.dict_tabulate(objects, is_list_dict=True)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(*OPTIONS_RUN_OFFLINE["args"], **OPTIONS_RUN_OFFLINE["kwargs"])
@click.option(
    *OPTIONS_RUN_OFFLINE_PATH_FROM["args"], **OPTIONS_RUN_OFFLINE_PATH_FROM["kwargs"]
)
@click.option(
    "--output",
    "-o",
    type=str,
    help="Optional flag to print the response as a json object or store the response as json file"
    "Example `-o json` or `-o path=./data.json`",
)
@click.pass_context
@clean_outputs
def get(ctx, project, uid, offline, path, output):
    """Get run.

    Uses /docs/core/cli/#caching

    Examples for getting a run:

    \b
    $ polyaxon ops get  # if run is cached

    \b
    $ polyaxon ops get --uid 8aac02e3a62a4f0aaa257c59da5eab80 # project is cached

    \b
    $ polyaxon ops get --project=cats-vs-dogs -uid 8aac02e3a62a4f0aaa257c59da5eab80

    \b
    $ polyaxon ops get -p alain/cats-vs-dogs --uid 8aac02e3a62a4f0aaa257c59da5eab80
    """

    uid = uid or ctx.obj.get("run_uuid")

    if offline:
        offline_path = ctx_paths.get_offline_path(
            entity_value=uid, entity_kind=V1ProjectFeature.RUNTIME, path=path
        )
        offline_path = "{}/{}".format(offline_path, ctx_paths.CONTEXT_LOCAL_RUN)
        if not os.path.exists(offline_path):
            Printer.error(
                f"Could not get offline run, the path `{offline_path}` "
                f"does not exist."
            )
            sys.exit(1)
        run_data = RunConfigManager.read_from_path(offline_path)
    else:
        owner, project_name, run_uuid = get_project_run_or_local(
            project or ctx.obj.get("project"),
            uid,
            is_cli=True,
        )

        try:
            polyaxon_client = RunClient(
                owner=owner,
                project=project_name,
                run_uuid=run_uuid,
                manual_exceptions_handling=True,
            )
            polyaxon_client.refresh_data()
            config = polyaxon_client.client.sanitize_for_serialization(
                polyaxon_client.run_data
            )
            cache.cache(
                config_manager=RunConfigManager,
                config=config,
                owner=owner,
                project=project_name,
            )
            if output:
                run_url = get_dashboard_url(
                    subpath="{}/{}/runs/{}".format(owner, project_name, run_uuid)
                )
                config["url"] = run_url
                handle_output(config, output)
                return
            run_data = polyaxon_client.run_data
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e,
                message="Could not load run `{}/{}/{}` info.".format(
                    owner, project_name, run_uuid
                ),
            )
            sys.exit(1)

    get_run_details(run_data)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Automatic yes to prompts. "
    'Assume "yes" as answer to all prompts and run non-interactively.',
)
@click.option(*OPTIONS_RUN_OFFLINE["args"], **OPTIONS_RUN_OFFLINE["kwargs"])
@click.option(
    *OPTIONS_RUN_OFFLINE_PATH_FROM["args"], **OPTIONS_RUN_OFFLINE_PATH_FROM["kwargs"]
)
@click.pass_context
@clean_outputs
def delete(ctx, project, uid, yes, offline, path):
    """Delete a run.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops delete

    \b
    $ polyaxon ops delete --uid 8aac02e3a62a4f0aaa257c59da5eab80  # project is cached

    \b
    $ polyaxon ops delete --project=cats-vs-dogs -uid 8aac02e3a62a4f0aaa257c59da5eab80
    """
    if offline:
        offline_path = ctx_paths.get_offline_path(
            entity_value=uid, entity_kind=V1ProjectFeature.RUNTIME, path=path
        )
        offline_path = "{}/{}".format(offline_path, ctx_paths.CONTEXT_LOCAL_RUN)
        if not os.path.exists(offline_path):
            Printer.error(
                f"Could not get offline run, the path `{offline_path}` "
                f"does not exist."
            )
            sys.exit(1)
        try:
            os.remove(offline_path)
        except OSError as e:
            Printer.error(
                f"Could not delete offline run, the path `{offline_path}` "
                f"Error %s." % e
            )
            sys.exit(1)
        return

    # Resume normal flow
    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    if not yes and not click.confirm(
        "Are sure you want to delete run `{}`".format(run_uuid)
    ):
        Printer.print("Exiting without deleting the run.")
        sys.exit(1)

    try:
        polyaxon_client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        polyaxon_client.delete()
        # Purge caching
        RunConfigManager.purge()
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not delete run `{}`.".format(run_uuid))
        sys.exit(1)

    Printer.success("Run `{}` was delete successfully".format(run_uuid))


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(*OPTIONS_NAME["args"], type=str, help="Name of the run (optional).")
@click.option("--description", type=str, help="Description of the run (optional).")
@click.option("--tags", type=str, help="Tags of the run (comma separated values).")
@click.option(*OPTIONS_RUN_OFFLINE["args"], **OPTIONS_RUN_OFFLINE["kwargs"])
@click.option(
    *OPTIONS_RUN_OFFLINE_PATH_FROM["args"], **OPTIONS_RUN_OFFLINE_PATH_FROM["kwargs"]
)
@click.pass_context
@clean_outputs
def update(ctx, project, uid, name, description, tags, offline, path):
    """Update run.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops update --uid 8aac02e3a62a4f0aaa257c59da5eab80
    --description="new description for my runs"

    \b
    $ polyaxon ops update --project=cats-vs-dogs -uid 8aac02e3a62a4f0aaa257c59da5eab80 --tags="foo, bar" --name="unique-name"
    """
    update_dict = {}

    if name:
        update_dict["name"] = name

    if description is not None:
        update_dict["description"] = description

    tags = validate_tags(tags, validate_yaml=True)
    if tags:
        update_dict["tags"] = tags

    if not update_dict:
        Printer.warning("No argument was provided to update the run.")
        sys.exit(0)

    if offline:
        offline_path = ctx_paths.get_offline_path(
            entity_value=uid, entity_kind=V1ProjectFeature.RUNTIME, path=path
        )
        offline_path = "{}/{}".format(offline_path, ctx_paths.CONTEXT_LOCAL_RUN)
        if not os.path.exists(offline_path):
            Printer.error(
                f"Could not get offline run, the path `{offline_path}` "
                f"does not exist."
            )
            sys.exit(1)
        try:
            response = RunConfigManager.read_from_path(offline_path)
            for k, v in update_dict.items():
                setattr(response, k, v)
            with open(offline_path, "w") as config_file:
                config_file.write(orjson_dumps(response.to_dict()))
            run_uuid = uid or response.uuid
        except OSError as e:
            Printer.error(
                f"Could not delete offline run, the path `{offline_path}` "
                f"Error %s." % e
            )
            sys.exit(1)
    else:
        owner, project_name, run_uuid = get_project_run_or_local(
            project or ctx.obj.get("project"),
            uid or ctx.obj.get("run_uuid"),
            is_cli=True,
        )
        try:
            polyaxon_client = RunClient(
                owner=owner,
                project=project_name,
                run_uuid=run_uuid,
                manual_exceptions_handling=True,
            )
            response = polyaxon_client.update(update_dict)
        except (ApiException, HTTPError) as e:
            handle_cli_error(e, message="Could not update run `{}`.".format(run_uuid))
            sys.exit(1)

    Printer.success("Run `{}` was updated.".format(run_uuid))
    get_run_details(response)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.pass_context
@clean_outputs
def approve(ctx, project, uid):
    """Approve a run waiting for human validation.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops approve

    \b
    $ polyaxon ops approve --uid 8aac02e3a62a4f0aaa257c59da5eab80
    """
    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )

    try:
        polyaxon_client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        polyaxon_client.approve()
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not approve run `{}`.".format(run_uuid))
        sys.exit(1)

    Printer.success("Run `{}` was approved".format(run_uuid))


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Automatic yes to prompts. "
    'Assume "yes" as answer to all prompts and run non-interactively.',
)
@click.pass_context
@clean_outputs
def stop(ctx, project, uid, yes):
    """Stop run.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops stop

    \b
    $ polyaxon ops stop --uid 8aac02e3a62a4f0aaa257c59da5eab80
    """
    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    if not yes and not click.confirm(
        "Are sure you want to stop " "run `{}`".format(run_uuid)
    ):
        Printer.print("Exiting without stopping run.")
        sys.exit(0)

    try:
        polyaxon_client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        polyaxon_client.stop()
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not stop run `{}`.".format(run_uuid))
        sys.exit(1)

    Printer.success("Run `{}` is being stopped ...".format(run_uuid))


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Automatic yes to prompts. "
    'Assume "yes" as answer to all prompts and run non-interactively.',
)
@click.pass_context
@clean_outputs
def skip(ctx, project, uid, yes):
    """Skip run.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops skip

    \b
    $ polyaxon ops skip --uid 8aac02e3a62a4f0aaa257c59da5eab80
    """
    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    if not yes and not click.confirm(
        "Are sure you want to stop " "run `{}`".format(run_uuid)
    ):
        Printer.print("Exiting without stopping run.")
        sys.exit(0)

    try:
        polyaxon_client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        polyaxon_client.skip()
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not skip run `{}`.".format(run_uuid))
        sys.exit(1)

    Printer.success("Run `{}` is skipped.".format(run_uuid))


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--name",
    type=str,
    help="Name to give to this run, must be unique within the project, could be none.",
)
@click.option("--tags", type=str, help="Tags of this run (comma separated values).")
@click.option("--description", type=str, help="The description to give to this run.")
@click.option(
    "--copy",
    "-c",
    is_flag=True,
    default=False,
    help="Copy mode clones the run before restarting instead "
    "to not mutate the current state of the run.",
)
@click.option(
    "--copy-dir",
    "copy_dirs",
    multiple=True,
    help="To copy specific dirs from the run's artifacts before restarting, "
    "you can pass multiple dirs to copy `--copy-dir dir1 --copy-dir path/to/dir2`.",
)
@click.option(
    "--copy-file",
    "copy_files",
    multiple=True,
    help="To copy specific dirs from the run's artifacts before restarting, "
    "you can pass multiple dirs to copy `--copy-file file1 --copy-file path/to/file2`.",
)
@click.option(
    "-f",
    "--file",
    "polyaxonfile",
    multiple=True,
    type=click.Path(exists=True),
    help="Optional polyaxonfile to use. The config passed will be treated as an override."
    "Use `--recompile` to use a full specification instead of an override/preset config.",
)
@click.option(
    "--recompile",
    is_flag=True,
    default=False,
    help="A flag to tell Polyaxon that polyaxonfile is a full specification.",
)
@click.pass_context
@clean_outputs
def restart(
    ctx,
    project,
    uid,
    name,
    tags,
    description,
    copy,
    copy_dirs,
    copy_files,
    polyaxonfile,
    recompile,
):
    """Restart run.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops restart

    \b
    $ polyaxon ops restart --uid 8aac02e3a62a4f0aaa257c59da5eab80
    """
    content = None
    if polyaxonfile:
        content = OperationSpecification.read(polyaxonfile, is_preset=True).to_json()

    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    try:
        polyaxon_client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        response = polyaxon_client.restart(
            name=name,
            description=description,
            tags=tags,
            content=content,
            recompile=recompile,
            copy=copy,
            copy_dirs=copy_dirs,
            copy_files=copy_files,
        )
        Printer.success(
            "Run was {} with uid {}".format(
                "copied" if copy else "restarted", response.uuid
            )
        )
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not restart run `{}`.".format(run_uuid))
        sys.exit(1)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--name",
    type=str,
    help="Name to give to this run, must be unique within the project, could be none.",
)
@click.option("--tags", type=str, help="Tags of this run (comma separated values).")
@click.option("--description", type=str, help="The description to give to this run.")
@click.option(
    "-f",
    "--file",
    "polyaxonfile",
    multiple=True,
    type=click.Path(exists=True),
    help="Optional polyaxonfile to use. The config passed will be treated as an override."
    "Use `--recompile` to use a full specification instead of an override/preset config.",
)
@click.option(
    "--recompile",
    is_flag=True,
    default=False,
    help="A flag to tell Polyaxon that polyaxonfile is a full specification.",
)
@click.pass_context
@clean_outputs
def resume(
    ctx,
    project,
    uid,
    name,
    tags,
    description,
    polyaxonfile,
    recompile,
):
    """Resume run.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops resume

    \b
    $ polyaxon ops resume --uid 8aac02e3a62a4f0aaa257c59da5eab80
    """
    content = None
    if polyaxonfile:
        content = OperationSpecification.read(polyaxonfile, is_preset=True).to_json()

    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    try:
        polyaxon_client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        response = polyaxon_client.resume(
            name=name,
            description=description,
            tags=tags,
            content=content,
            recompile=recompile,
        )
        Printer.success("Run was resumed with uid {}".format(response.uuid))
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not resume run `{}`.".format(run_uuid))
        sys.exit(1)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.pass_context
@clean_outputs
def invalidate(ctx, project, uid):
    """Invalidate the run's cache state.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops invalidate

    \b
    $ polyaxon ops invalidate --uid 8aac02e3a62a4f0aaa257c59da5eab80
    """
    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    try:
        polyaxon_client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        response = polyaxon_client.invalidate()
        Printer.success("Run `{}` was invalidated".format(response.uuid))
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not invalidate run `{}`.".format(run_uuid))
        sys.exit(1)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--executor",
    "-exc",
    type=str,
    help="The executor to use, possible values are: docker, k8s, process.",
)
@click.pass_context
@clean_outputs
def execute(ctx, project, uid, executor):
    """Execute a run on the current local machine using one of the specified executor.

    Uses /docs/core/cli/#caching

    Examples getting executing a run:

    \b
    $ polyaxon ops execute

    \b
    $ polyaxon ops execute -uid 8aac02e3a62a4f0aaa257c59da5eab80
    """

    Printer.warning(
        "The `ops execute` command is experimental and might change in the future!"
    )

    def _execute_on_docker(response: V1Run, run_client: RunClient):
        from polyaxon._docker.executor import Executor

        run_client.log_status(
            V1Statuses.STARTING,
            reason="CliDockerExecutor",
            message="Operation is starting",
        )
        executor = Executor()
        if not executor.manager.check():
            run_client.log_failed(
                reason="CliDockerExecutor",
                message="Docker is required to run this operation.",
            )
            raise Printer.error(
                "Docker is required to run this command.", sys_exit=True
            )
        run_client.log_status(
            V1Statuses.RUNNING,
            reason="CliDockerExecutor",
            message="Operation is running",
        )
        if V1RunKind.has_pipeline(response.kind):
            has_children = True
            while has_children:
                pipeline_runs = run_client.list_children(
                    query="status:created", sort="created_at", limit=1
                )
                if pipeline_runs.results:
                    current_run_client = RunClient(
                        owner=owner,
                        project=project_name,
                        run_uuid=pipeline_runs.results[0].uuid,
                        manual_exceptions_handling=True,
                    )
                    current_run_client.refresh_data()
                    _prepare(current_run_client.run_data, current_run_client)
                    _execute(current_run_client.run_data, current_run_client)
                else:
                    has_children = False
            return
        else:
            result = executor.create_from_run(response, default_auth=not is_in_ce())
        if result["status"] == V1Statuses.SUCCEEDED:
            run_client.log_succeeded(
                reason="CliDockerExecutor", message="Operation was succeeded"
            )
        else:
            run_client.log_failed(
                reason="CliDockerExecutor",
                message="Operation failed.\n{}".format(result["message"]),
            )

    def _execute_on_k8s(response: V1Run, run_client: RunClient):
        from polyaxon._k8s.executor.executor import Executor

        run_client.log_status(
            V1Statuses.STARTING,
            reason="CliK8SExecutor",
            message="Operation is starting",
        )
        if not settings.AGENT_CONFIG.namespace:
            run_client.log_failed(
                reason="CliK8SExecutor",
                message="an agent config with defined namespace is required.",
            )
            raise Printer.error(
                "Agent config requires a namespace to be set.", sys_exit=True
            )

        executor = Executor(namespace=settings.AGENT_CONFIG.namespace)
        if not executor.manager.get_version():
            run_client.log_failed(
                reason="CliK8SExecutor",
                message="Kubernetes is required to run this operation.",
            )
            raise Printer.error(
                "Kubernetes is required to run this command.", sys_exit=True
            )
        run_client.log_status(
            V1Statuses.RUNNING,
            reason="CliK8SExecutor",
            message="Operation is running",
        )
        executor.create_from_run(response, default_auth=not is_in_ce())

    def _execute_on_local_process(response: V1Run, run_client: RunClient):
        from polyaxon._local_process.executor import Executor

        run_client.log_status(
            V1Statuses.STARTING,
            reason="CliProcessExecutor",
            message="Operation is starting",
        )
        executor = Executor()
        if not executor.manager.check():
            run_client.log_failed(
                reason="CliProcessExecutor",
                message="Local process can't be used to run this operation.",
            )
            raise Printer.error(
                "Local process can't be used to run this operation.", sys_exit=True
            )

        run_client.log_status(
            V1Statuses.RUNNING,
            reason="CliProcessExecutor",
            message="Operation is running",
        )

        if V1RunKind.has_pipeline(response.kind):
            has_children = True
            while has_children:
                pipeline_runs = run_client.list_children(
                    query="status:created", sort="created_at", limit=1
                )
                if pipeline_runs.results:
                    current_run_client = RunClient(
                        owner=owner,
                        project=project_name,
                        run_uuid=pipeline_runs.results[0].uuid,
                        manual_exceptions_handling=True,
                    )
                    current_run_client.refresh_data()
                    _prepare(current_run_client.run_data, current_run_client)
                    _execute(current_run_client.run_data, current_run_client)
                else:
                    has_children = False
            return
        else:
            result = executor.create_from_run(response, default_auth=not is_in_ce())
        if result["status"] == V1Statuses.SUCCEEDED:
            run_client.log_succeeded(
                reason="CliProcessExecutor", message="Operation was succeeded"
            )
        else:
            run_client.log_failed(
                reason="CliProcessExecutor",
                message="Operation failed.\n{}".format(result["message"]),
            )

    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )

    try:
        polyaxon_client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        polyaxon_client.refresh_data()
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not execute run `{}`.".format(run_uuid))
        sys.exit(1)

    executor = executor or ctx.obj.get("executor") or RunnerKind.DOCKER
    if not settings.AGENT_CONFIG:
        settings.set_agent_config()
        if not settings.AGENT_CONFIG.artifacts_store:
            if executor == RunnerKind.K8S:
                polyaxon_client.log_failed(
                    reason="CliK8SExecutor",
                    message="Could not resolve an agent configuration.",
                )
                raise Printer.error(
                    "Could not resolve an agent configuration.", sys_exit=True
                )
            settings.AGENT_CONFIG.set_default_artifacts_store()

    def _prepare(response: V1Run, client: RunClient):
        if response.status == V1Statuses.CREATED:
            try:
                client.approve()
                client.refresh_data()
            except (ApiException, HTTPError) as e:
                handle_cli_error(
                    e, message="Could not approve run `{}`.".format(response.uuid)
                )
                sys.exit(1)

    def _execute(response: V1Run, client: RunClient):
        if LifeCycle.is_done(response.status):
            return
        if response.status != V1Statuses.COMPILED:
            Printer.error("Run must be compiled.", sys_exit=True)
        client.log_status(
            V1Statuses.SCHEDULED,
            reason="CliExecutor",
            message="Operation is pulled by CLI.",
        )
        if executor == RunnerKind.DOCKER:
            _execute_on_docker(response, client)
        elif executor == RunnerKind.K8S:
            _execute_on_k8s(response, client)
        elif executor == RunnerKind.PROCESS:
            _execute_on_local_process(response, client)
        else:
            client.log_failed(
                reason="CliExecutor",
                message="Local executor is not supported {}.".format(executor),
            )

    try:
        _prepare(polyaxon_client.run_data, polyaxon_client)
        _execute(polyaxon_client.run_data, polyaxon_client)
    except KeyboardInterrupt:
        polyaxon_client.log_failed(
            reason="CliExecutor",
            message="Operation was canceled with `KeyboardInterrupt`.",
        )
        sys.exit(1)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option("--watch", "-w", is_flag=True, help="Watch statuses.")
@click.option(*OPTIONS_RUN_OFFLINE["args"], **OPTIONS_RUN_OFFLINE["kwargs"])
@click.option(
    *OPTIONS_RUN_OFFLINE_PATH_FROM["args"], **OPTIONS_RUN_OFFLINE_PATH_FROM["kwargs"]
)
@click.pass_context
@clean_outputs
def statuses(ctx, project, uid, watch, offline, path):
    """Get run's statuses.

    Uses /docs/core/cli/#caching

    Examples getting run statuses:

    \b
    $ polyaxon ops statuses

    \b
    $ polyaxon ops statuses -uid 8aac02e3a62a4f0aaa257c59da5eab80
    """
    if offline:
        offline_path = ctx_paths.get_offline_path(
            entity_value=uid, entity_kind=V1ProjectFeature.RUNTIME, path=path
        )
        offline_path = "{}/{}".format(offline_path, ctx_paths.CONTEXT_LOCAL_RUN)
        if not os.path.exists(offline_path):
            Printer.error(
                f"Could not get offline run, the path `{offline_path}` "
                f"does not exist."
            )
            sys.exit(1)
        table = Printer.get_table()
        try:
            response = RunConfigManager.read_from_path(offline_path)
            status, conditions = response.status, response.status_conditions
            handle_run_statuses(status, conditions, table)
            Printer.print(table)
        except OSError as e:
            Printer.error(
                f"Could not get offline run, the path `{offline_path}` "
                f"Error %s." % e
            )
            sys.exit(1)
        return

    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )

    client = RunClient(
        owner=owner,
        project=project_name,
        run_uuid=run_uuid,
        manual_exceptions_handling=True,
    )
    table = Printer.get_table()
    if watch:
        with Printer.get_live() as live:
            try:
                for status, conditions in client.watch_statuses():
                    updated = handle_run_statuses(status, conditions, table)
                    if updated:
                        live.update(table)
            except (ApiException, HTTPError, PolyaxonClientException) as e:
                handle_cli_error(
                    e, message="Could get status for run `{}`.".format(run_uuid)
                )
                sys.exit(1)
    else:
        try:
            status, conditions = client.get_statuses()
            handle_run_statuses(status, conditions, table)
            Printer.print(table)
        except (ApiException, HTTPError, PolyaxonClientException) as e:
            handle_cli_error(
                e, message="Could get status for run `{}`.".format(run_uuid)
            )
            sys.exit(1)


# @ops.command()
# @click.option("--gpu", "-g", is_flag=True, help="List run GPU resources.")
# @click.pass_context
# def resources(ctx, gpu):
#     """Get run or run job resources.
#
#     Uses /docs/core/cli/#caching
#
#     Examples for getting run resources:
#
#     \b
#     $ polyaxon ops resources -uid 8aac02e3a62a4f0aaa257c59da5eab80
#
#     For GPU resources
#
#     \b
#     $ polyaxon ops resources -uid 8aac02e3a62a4f0aaa257c59da5eab80 --gpu
#     """
#
#     def get_run_resources():
#         try:
#             message_handler = Printer.gpu_resources if gpu else Printer.resources
#             PolyaxonClient().run.resources(
#                 owner, project_name, run_uuid, message_handler=message_handler
#             )
#         except (ApiException, HTTPError) as e:
#             handle_cli_error(
#                 e, message="Could not get resources for run `{}`.".format(run_uuid)
#             )
#             sys.exit(1)
#
#     owner, project_name, run_uuid = get_project_run_or_local(
#         ctx.obj.get("project"), ctx.obj.get("run_uuid"), is_cli=True,
#     )
#
#     get_run_resources()


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--follow",
    "-f",
    is_flag=True,
    default=True,
    help="Stream logs after showing past logs.",
)
@click.option(
    "--hide-time",
    "-h",
    is_flag=True,
    default=False,
    help="Whether or not to hide timestamps from the log stream.",
)
@click.option(
    "--all-containers",
    is_flag=True,
    default=False,
    help="Whether to stream logs from all containers.",
)
@click.option(
    "--all-info",
    "-a",
    is_flag=True,
    default=False,
    help="Whether to show all information including container names, pod names, and node names.",
)
@click.option(*OPTIONS_RUN_OFFLINE["args"], **OPTIONS_RUN_OFFLINE["kwargs"])
@click.option(
    *OPTIONS_RUN_OFFLINE_PATH_FROM["args"], **OPTIONS_RUN_OFFLINE_PATH_FROM["kwargs"]
)
@click.pass_context
@clean_outputs
def logs(ctx, project, uid, follow, hide_time, all_containers, all_info, offline, path):
    """Get run's logs.

    Uses /docs/core/cli/#caching

    Examples for getting run logs:

    \b
    $ polyaxon run logs

    \b
    $ polyaxon ops logs -uid 8aac02e3a62a4f0aaa257c59da5eab80 -p mnist
    """
    if offline:
        offline_path = ctx_paths.get_offline_path(
            entity_value=uid, entity_kind=V1ProjectFeature.RUNTIME, path=path
        )
        logs_path = "{}/plxlogs".format(offline_path)
        offline_path = "{}/{}".format(offline_path, ctx_paths.CONTEXT_LOCAL_RUN)
        if not os.path.exists(offline_path):
            Printer.error(
                f"Could not get offline run, the path `{offline_path}` "
                f"does not exist."
            )
            sys.exit(1)
        else:
            response = RunConfigManager.read_from_path(offline_path)
            Printer.print(
                "Loading logs for run {}<{}> from path `{}`".format(
                    response.name, uid, logs_path
                )
            )

        try:
            from traceml.logging.streamer import get_logs_streamer, load_logs_from_path

            load_logs_from_path(
                logs_path=logs_path,
                hide_time=hide_time,
                all_containers=all_containers,
                all_info=all_info,
            )
        except OSError as e:
            Printer.error(
                f"Could not get offline run, the path `{logs_path}` " f"Error %s." % e
            )
            sys.exit(1)
        return

    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    client = RunClient(
        owner=owner,
        project=project_name,
        run_uuid=run_uuid,
        manual_exceptions_handling=True,
    )

    try:
        get_run_logs(
            client=client,
            hide_time=hide_time,
            all_containers=all_containers,
            all_info=all_info,
            follow=follow,
        )
    except (ApiException, HTTPError, PolyaxonClientException) as e:
        handle_cli_error(
            e,
            message="Could not get logs for run `{}`.".format(client.run_uuid),
        )
        sys.exit(1)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.pass_context
@clean_outputs
def inspect(ctx, project, uid):
    """Inspect a run.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops inspect -uid 8aac02e3a62a4f0aaa257c59da5eab80

    \b
    $ polyaxon ops inspect -p acme/project -uid 8aac02e3a62a4f0aaa257c59da5eab80
    """
    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    try:
        client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        handle_output(client.inspect(), output="json")
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not inspect the run `{}`.".format(run_uuid))
        sys.exit(1)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--command",
    "-cmd",
    type=str,
    help="Path to download, if not provided the full run's  artifacts will downloaded.",
)
@click.option(
    "--pod",
    type=str,
    help="Optional. In a multi-replica or distributed job, "
    "the pod to use for selecting the container.",
)
@click.option(
    "--container",
    type=str,
    help="Optional. The container to use for starting the shell session, "
    "by default the main container is used..",
)
@click.pass_context
@clean_outputs
def shell(ctx, project, uid, command, pod, container):
    """Start a shell session for run.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops shell -uid 8aac02e3a62a4f0aaa257c59da5eab80

    \b
    $ polyaxon ops shell -p acme/project -uid 8aac02e3a62a4f0aaa257c59da5eab80 --command=python

    \b
    $ polyaxon ops shell -p acme/project -uid 8aac02e3a62a4f0aaa257c59da5eab80 -cmd="/bin/bash"
    """
    from polyaxon._vendor.shell_pty import PseudoTerminal

    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    client = RunClient(
        owner=owner,
        project=project_name,
        run_uuid=run_uuid,
        manual_exceptions_handling=True,
    )

    wait_for_running_condition(client)

    Printer.success("Starting a new shell session...")
    try:
        pty = PseudoTerminal(
            client_shell=client.shell(command=command, pod=pod, container=container)
        )
        pty.start(sys.argv[1:])
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not inspect the run `{}`.".format(run_uuid))
        sys.exit(1)
    Printer.header("Disconnecting...")


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "-f",
    "--file",
    "files",
    type=str,
    multiple=True,
    help="Optional list of files to download.",
)
@click.option(
    "-d",
    "--dir",
    "dirs",
    type=str,
    multiple=True,
    help="Optional list of dirs to download.",
)
@click.option(
    "-l-name",
    "--lineage-name",
    "lineage_names",
    type=str,
    multiple=True,
    help="Optional list of artifact lineage name references.",
)
@click.option(
    "-l-kind",
    "--lineage-kind",
    "lineage_kinds",
    type=str,
    multiple=True,
    help="Optional list of artifact lineage kind references.",
)
@click.option(
    "--path",
    "--path-to",
    "path_to",
    type=click.Path(exists=False),
    help="The destination where to download the artifacts.",
)
@click.option(
    "--no-untar",
    is_flag=True,
    default=False,
    help="Disable the automatic untar of the downloaded artifacts.",
)
@click.pass_context
@clean_outputs
def artifacts(
    ctx, project, uid, files, dirs, lineage_names, lineage_kinds, path_to, no_untar
):
    """Download outputs/artifacts for run.

    If no files, dirs, or refs are provided, the full run's artifacts will be downloaded.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops artifacts -uid 8aac02e3a62a4f0aaa257c59da5eab80

    \b
    $ polyaxon ops artifacts -uid 8aac02e3a62a4f0aaa257c59da5eab80 --dir "uploads/path/dir"

    \b
    $ polyaxon ops artifacts -uid 8aac02e3a62a4f0aaa257c59da5eab80 -f "outputs/path/file1" --file="outputs/path/file2" -d "outputs/path/dir1"

    \b
    $ polyaxon ops artifacts -uid 8aac02e3a62a4f0aaa257c59da5eab80 --path="this/path"

    \b
    $ polyaxon ops artifacts -uid 8aac02e3a62a4f0aaa257c59da5eab80 -l-name image-example -l-name debug-csv-file --path="this/path"

    \b
    $ polyaxon ops artifacts -uid 8aac02e3a62a4f0aaa257c59da5eab80 -l-kind model -l-kind env --path="this/path"
    """
    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    client = RunClient(
        owner=owner,
        project=project_name,
        run_uuid=run_uuid,
        manual_exceptions_handling=True,
    )

    files = to_list(files, check_none=True)
    dirs = to_list(dirs, check_none=True)
    lineage_names = to_list(lineage_names, check_none=True)
    lineage_kinds = to_list(lineage_kinds, check_none=True)

    def _download_all():
        Printer.header("Downloading all run's artifacts")
        try:
            download_path = client.download_artifacts(
                path="", path_to=path_to, untar=not no_untar
            )
            Printer.success(
                "All run's artifacts downloaded. Path: {}".format(download_path)
            )
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e, message="Could not download artifacts for run `{}`.".format(run_uuid)
            )
            sys.exit(1)

    if not any([files, dirs, lineage_names, lineage_kinds]):
        _download_all()

    def _download_file():
        Printer.header(f"Downloading file path {f} ...")
        try:
            download_path = client.download_artifact(
                path=f,
                path_to=path_to,
            )
            Printer.success("File path {} downloaded to {}".format(f, download_path))
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e,
                message="Could not download file path {} for run `{}`.".format(
                    f, run_uuid
                ),
            )

    for f in files:
        _download_file()

    def _download_dir():
        Printer.header(f"Downloading dir path {f} ...")
        try:
            download_path = client.download_artifacts(
                path=f, path_to=path_to, untar=not no_untar
            )
            Printer.success("Dir path {} downloaded to {}".format(f, download_path))
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e,
                message="Could not download dir path {} for run `{}`.".format(
                    f, run_uuid
                ),
            )

    for f in dirs:
        _download_dir()

    # collecting all artifact lineage reference
    lineages = []
    if lineage_names:
        query = "name: {}".format("|".join(lineage_names))
        try:
            lineages += client.get_artifacts_lineage(query=query, limit=1000).results
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e,
                message="Could not get artifacts lineage for run `{}` and artifacts name `{}`.".format(
                    run_uuid,
                    lineage_names,
                ),
            )
    if lineage_kinds:
        query = "kind: {}".format("|".join(lineage_kinds))
        try:
            lineages += client.get_artifacts_lineage(query=query, limit=1000).results
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e,
                message="Could not get artifacts lineage for run `{}` and artifacts name `{}`.".format(
                    run_uuid,
                    lineages,
                ),
            )

    if lineages:
        Printer.print("Loaded artifact lineage information for run {}".format(run_uuid))

    # To avoid duplicates
    lineage_keys = set([])

    def _download_lineage():
        lineage_def = "artifact lineage {} (kind: {})".format(
            lineage.name, lineage.kind
        )
        Printer.header(
            f"Downloading assets for {lineage_def} ...",
        )
        try:
            download_path = client.download_artifact_for_lineage(
                lineage=lineage, path_to=path_to
            )
            Printer.success(
                "Assets for {} downloaded to {}".format(lineage_def, download_path)
            )
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e,
                message="Could not download assets for {} under run `{}`.".format(
                    lineage_def, run_uuid
                ),
            )

    for lineage in lineages:
        if lineage.name in lineage_keys:
            continue
        else:
            lineage_keys.add(lineage.name)

        _download_lineage()


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--path-from",
    type=click.Path(exists=False),
    help="The path to upload from relative the current location (or absolute path), "
    "Note that this must be a valid path, or the CLI will raise an error. "
    "Defaults to the current path.",
)
@click.option(
    "--path-to",
    type=str,
    help="The destination where to upload the artifacts. "
    "If the path is '/' the root artifacts path of the run will be used, "
    "otherwise the values should start without the separator, "
    "e.g. `uploads`, `code`, `dataset/images/values`, ...",
)
@click.option(
    "--sync-failure",
    is_flag=True,
    default=False,
    help="To set the run to failed if the upload fails.",
)
@click.pass_context
@clean_outputs
def upload(ctx, project, uid, path_from, path_to, sync_failure):
    """Upload runs' artifacts.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops upload -uid 8aac02e3a62a4f0aaa257c59da5eab80

    \b
    $ polyaxon ops upload -uid 8aac02e3a62a4f0aaa257c59da5eab80 --path-from="path/to/upload"

    \b
    $ polyaxon ops upload -uid 8aac02e3a62a4f0aaa257c59da5eab80 --path-to="path/to/upload/to"
    """
    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    is_file = os.path.isfile(path_from) if path_from else False
    try:
        client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        if is_file:
            response = client.upload_artifact(
                filepath=path_from, path=path_to, overwrite=True
            )
        else:
            response = client.upload_artifacts_dir(
                dirpath=path_from,
                path=path_to,
                overwrite=True,
                relative_to=path_from,
            )
    except (
        ApiException,
        HTTPError,
        PolyaxonHTTPError,
        PolyaxonShouldExitError,
        PolyaxonClientException,
    ) as e:
        handle_cli_error(
            e, message="Could not upload artifacts for run `{}`".format(run_uuid)
        )
        sys.exit(1)

    if response and response.status_code == 200:
        Printer.success("Artifacts uploaded")
    else:
        if sync_failure:
            client.log_failed(
                reason="OperationCli", message="Operation failed uploading artifacts"
            )
        message = "Error uploading artifacts. "
        if response:
            message += "Status: {}. Error: {}.".format(
                response.status_code, response.content
            )
        Printer.error(message, sys_exit=True)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--to-project",
    "-to",
    help="The project to transfer the operation/run to.",
)
@click.pass_context
@clean_outputs
def transfer(ctx, project, uid, to_project):
    """Transfer the run to a destination project under the same owner/organization.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops transfer --to-project dest-project

    \b
    $ polyaxon ops transfer -p acme/foobar -uid 8aac02e3a62a4f0aaa257c59da5eab80 -to=dest-project
    """
    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )

    try:
        polyaxon_client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )
        polyaxon_client.transfer(to_project=to_project)
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not transfer run `{}`.".format(run_uuid))
        sys.exit(1)

    Printer.success("Run `{}` was transferred.".format(run_uuid))


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Automatic yes to prompts. "
    'Assume "yes" as answer to all prompts and run non-interactively.',
)
@click.option(
    "--url",
    is_flag=True,
    default=False,
    help="Print the url of the dashboard for this run.",
)
@click.option(*OPTIONS_RUN_OFFLINE["args"], **OPTIONS_RUN_OFFLINE["kwargs"])
@click.option(
    *OPTIONS_RUN_OFFLINE_PATH_FROM["args"], **OPTIONS_RUN_OFFLINE_PATH_FROM["kwargs"]
)
@click.option(
    "--server-config",
    "--sconfig",
    "-SC",
    metavar="NAME=VALUE",
    multiple=True,
    help="A configuration to override the default options for the local streaming server of the run, "
    "form `-SC key=value` or `--server-config key=value` or `--sconfig key=value`.",
)
@click.pass_context
@clean_outputs
def dashboard(ctx, project, uid, yes, url, offline, path, server_config):
    """Open this operation's dashboard details in browser."""
    if offline:
        offline_path = ctx_paths.get_offline_path(
            entity_value=uid, entity_kind=V1ProjectFeature.RUNTIME, path=path
        )
        offline_path = "{}/{}".format(offline_path, ctx_paths.CONTEXT_LOCAL_RUN)
        if not os.path.exists(offline_path):
            Printer.error(
                f"Could not get offline run, the path `{offline_path}` "
                f"does not exist."
            )
            sys.exit(1)
        run_data = RunConfigManager.read_from_path(offline_path)
        owner, project_name, run_uuid = run_data.owner, run_data.project, run_data.uuid
    else:
        owner, project_name, run_uuid = get_project_run_or_local(
            project or ctx.obj.get("project"),
            uid or ctx.obj.get("run_uuid"),
            is_cli=True,
        )
    subpath = "{}/{}/runs/{}".format(owner, project_name, run_uuid)
    dashboard_url = get_dashboard_url(subpath=subpath)
    get_dashboard(dashboard_url=dashboard_url, url_only=url, yes=yes)
    if offline:
        from haupt.cli.viewer import sanitize_server_config, viewer

        os.environ["POLYAXON_DASHBOARD_URL"] = dashboard_url
        server_config = sanitize_server_config(server_config)
        ctx.invoke(viewer, path=path, **server_config)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Automatic yes to prompts. "
    'Assume "yes" as answer to all prompts and run non-interactively.',
)
@click.option(
    "--external",
    is_flag=True,
    default=False,
    help="Open the external service URL.",
)
@click.option(
    "--url",
    is_flag=True,
    default=False,
    help="Print the url of the dashboard or external service.",
)
@click.pass_context
@clean_outputs
def service(ctx, project, uid, yes, external, url):
    """Open the operation service in browser.

    N.B. The operation must have a run kind service, otherwise it will raise an error.

    You can open the service embedded in Polyaxon UI or using the real service URL,
    please use the `--external` flag.
    """
    owner, project_name, run_uuid = get_project_run_or_local(
        project or ctx.obj.get("project"),
        uid or ctx.obj.get("run_uuid"),
        is_cli=True,
    )
    client = RunClient(
        owner=owner,
        project=project_name,
        run_uuid=run_uuid,
        manual_exceptions_handling=True,
    )
    try:
        client.refresh_data()
    except (
        ApiException,
        HTTPError,
        PolyaxonHTTPError,
        PolyaxonShouldExitError,
        PolyaxonClientException,
    ) as e:
        handle_cli_error(
            e, message="Could not find run `{}`.".format(run_uuid), sys_exit=True
        )

    if client.run_data.kind != V1RunKind.SERVICE:
        Printer.warning(
            "Command expected an operation of "
            "kind `service` received kind: `{}`!".format(client.run_data.kind)
        )
        sys.exit(1)

    wait_for_running_condition(client)

    run_url = get_dashboard_url(
        subpath="{}/{}/runs/{}/service".format(owner, project_name, run_uuid)
    )

    namespace = client.run_data.settings.namespace
    is_external = client.run_data.meta_info.get(META_IS_EXTERNAL, False)
    rewrite_path = client.run_data.meta_info.get(META_REWRITE_PATH, False)
    service_endpoint = EXTERNAL_V1 if is_external else SERVICES_V1
    if rewrite_path:
        service_endpoint = REWRITE_EXTERNAL_V1 if is_external else REWRITE_SERVICES_V1

    service_subpath = "{}/{}/{}/runs/{}/".format(
        namespace, owner, project_name, run_uuid
    )
    port = 80
    if client.settings and client.settings.agent:
        version = client.settings.agent.version
        if version and compare_versions(version, "2.0.0", ">="):
            ports = client.run_data.meta_info.get(META_PORTS, [])
            port = ports[0] if ports else 80
        else:
            port = None
    if port:
        service_subpath = "{}{}/".format(service_subpath, port)

    external_run_url = get_dashboard_url(
        base=service_endpoint,
        subpath=service_subpath,
    )

    if url:
        Printer.header("The service will be available at: {}".format(run_url))
        Printer.header(
            "You can also view it in an external link at: {}".format(external_run_url)
        )
        sys.exit(0)
    if not yes:
        click.confirm(
            "Dashboard page will now open in your browser. Continue?",
            abort=True,
            default=True,
        )
    if external:
        click.launch(external_run_url)
        sys.exit(0)
    click.launch(run_url)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--all-runs",
    "-a",
    is_flag=True,
    default=False,
    help="To pull all runs.",
)
@click.option(
    "--query", "-q", type=str, help="To filter the runs based on a query spec."
)
@click.option("--limit", "-l", type=int, help="To limit the list of runs.")
@click.option("--offset", "-off", type=int, help="To offset the list of runs.")
@click.option(
    "--no-artifacts",
    is_flag=True,
    default=False,
    help="To disable downloading the run's artifacts and only persist the metadata. "
    "This is useful if you want to move a run from one Polyaxon deployment "
    "to another while keeping the same artifacts store.",
)
@click.option(
    *OPTIONS_RUN_OFFLINE_PATH_TO["args"], **OPTIONS_RUN_OFFLINE_PATH_TO["kwargs"]
)
@click.pass_context
@clean_outputs
def pull(
    ctx,
    project,
    uid,
    all_runs,
    query,
    limit,
    offset,
    no_artifacts,
    path,
):
    """Pull a remote run or multiple remote runs to a local path.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops pull -uid 8aac02e3a62a4f0aaa257c59da5eab80

    \b
    $ polyaxon ops pull -uid 8aac02e3a62a4f0aaa257c59da5eab80 --no-artifacts

    \b
    $ polyaxon ops pull -uid 8aac02e3a62a4f0aaa257c59da5eab80 --path /tmp/base

    \b
    $ polyaxon ops pull -q "status: succeeded, kind: job, metrics.loss: <0.2" --l 10 --path /tmp/base

    \b
    $ polyaxon ops pull -a
    """
    owner, project_name = get_project_or_local(
        project or ctx.obj.get("project"), is_cli=True
    )

    def _pull(run_uuid: str):
        client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            manual_exceptions_handling=True,
        )

        try:
            Printer.header(f"Pulling remote run {run_uuid}")
            run_path = client.pull_remote_run(
                path=path,
                download_artifacts=not no_artifacts,
            )
            Printer.success(f"Finished pulling run {run_uuid} to {run_path}")
        except (
            ApiException,
            HTTPError,
            PolyaxonHTTPError,
            PolyaxonShouldExitError,
            PolyaxonClientException,
        ) as e:
            handle_cli_error(e, message="Could not pull run `{}`.".format(run_uuid))

    if all_runs or any([query, limit, offset]):
        limit = 1000 if all_runs else limit
        try:
            polyaxon_client = RunClient(
                owner=owner, project=project_name, manual_exceptions_handling=True
            )
            runs = polyaxon_client.list(
                limit=limit,
                offset=offset,
                query=query,
            ).results
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e, message="Could not get runs for project `{}`.".format(project_name)
            )
            sys.exit(1)
        Printer.header(f"Pulling remote runs (total: {len(runs)})...")
        for idx, run in enumerate(runs):
            Printer.heading(f"Pulling run {idx + 1}/{len(runs)} ...")
            _pull(run.uuid)
    elif uid:
        _pull(uid)
    else:
        Printer.error(
            "Please provide a run uuid, provide a query to filter runs, "
            "or pass the flag `-a/--all` to pull runs."
        )
        sys.exit(1)


@ops.command()
@click.option(*OPTIONS_PROJECT["args"], **OPTIONS_PROJECT["kwargs"])
@click.option(*OPTIONS_RUN_UID["args"], **OPTIONS_RUN_UID["kwargs"])
@click.option(
    "--all-runs",
    "-a",
    is_flag=True,
    default=False,
    help="To push all runs.",
)
@click.option(
    "--no-artifacts",
    is_flag=True,
    default=False,
    help="To disable uploading artifacts and only sync metadata. "
    "This is useful if you want to move a run from one Polyaxon deployment "
    "to another while keeping the same artifacts store (no artifacts transfer).",
)
@click.option(
    "--clean",
    "-c",
    is_flag=True,
    default=False,
    help="To clean the run(s) local data after syncing.",
)
@click.option(
    *OPTIONS_RUN_OFFLINE_PATH_FROM["args"], **OPTIONS_RUN_OFFLINE_PATH_FROM["kwargs"]
)
@click.option(
    "--reset-project",
    is_flag=True,
    default=False,
    help="Optional, to ignore the owner/project of the local "
    "run and use the owner/project provided or resolved from the current project.",
)
@click.pass_context
@clean_outputs
def push(ctx, project, uid, all_runs, no_artifacts, clean, path, reset_project):
    """Push a local run (or all runs) to a remove server.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon ops push -a --clean

    \b
    $ polyaxon ops push --path /tmp/experiments --clean

    \b
    $ polyaxon ops push -uid 8aac02e3a62a4f0aaa257c59da5eab80 --no-artifacts

    \b
    $ polyaxon ops push -uid 8aac02e3a62a4f0aaa257c59da5eab80 --clean

    \b
    $ polyaxon ops push -uid 8aac02e3a62a4f0aaa257c59da5eab80 --reset-project

    \b
    $ polyaxon ops push -uid 8aac02e3a62a4f0aaa257c59da5eab80 --reset-project -p send-to-project
    """
    owner, project_name = get_project_or_local(
        project or ctx.obj.get("project"), is_cli=True
    )

    offline_path = ctx_paths.get_offline_base_path(
        entity_kind=V1ProjectFeature.RUNTIME, path=path
    )

    def _push(run_uuid: str):
        Printer.header(f"Pushing offline run {run_uuid}")
        client = RunClient(
            owner=owner,
            project=project_name,
            run_uuid=run_uuid,
            is_offline=True,
            manual_exceptions_handling=True,
        )
        artifacts_path = "{}/{}".format(offline_path, run_uuid)
        try:
            client.load_offline_run(
                path=artifacts_path,
                run_client=client,
                reset_project=reset_project,
                raise_if_not_found=True,
            )
        except Exception as e:
            handle_cli_error(
                e, message="Could not load offline run `{}`.".format(run_uuid)
            )
            return

        Printer.success(
            f"Offline run {uid} loaded, start pushing to {client.owner}/{client.project} ..."
        )
        try:
            client.push_offline_run(
                path=artifacts_path,
                upload_artifacts=not no_artifacts,
                clean=clean,
            )
            Printer.success(
                f"Finished pushing offline run {uid} to {client.owner}/{client.project}"
            )
        except (
            ApiException,
            HTTPError,
            PolyaxonHTTPError,
            PolyaxonShouldExitError,
            PolyaxonClientException,
        ) as e:
            handle_cli_error(
                e, message="Could not push offline run `{}`.".format(run_uuid)
            )
            return

    if all_runs:
        if (
            not os.path.exists(offline_path)
            or not os.path.isdir(offline_path)
            or not os.listdir(offline_path)
        ):
            Printer.error(
                f"Could not push offline runs, the path `{offline_path}` "
                f"does not exist, is not a directory, or is empty."
            )
            sys.exit(1)
        run_paths = os.listdir(offline_path)
        Printer.header(f"Pushing local runs (total: {len(run_paths)}) ...")
        for idx, uid in enumerate(run_paths):
            Printer.heading(f"Pushing run {idx + 1}/{len(run_paths)} ...")
            _push(uid)
    elif uid:
        _push(uid)
    else:
        Printer.error(
            "Please provide a run uuid or pass the flag `-a/--all` to push all available runs."
        )
        sys.exit(1)


def _wait_for_running_condition(client: RunClient, live_update: Any):
    client.refresh_data()
    if LifeCycle.is_running(client.run_data.status):
        return

    client.wait_for_condition(
        statuses={V1Statuses.RUNNING} | LifeCycle.DONE_VALUES,
        live_update=live_update,
    )

    client.refresh_data()
    if LifeCycle.is_done(client.run_data.status):
        latest_status = Printer.add_status_color(
            {"status": client.run_data.status}, status_key="status"
        )
        live_update.update(
            status="The operation has reached a final status: {}\n.".format(
                latest_status["status"]
            )
        )
        sys.exit()


def wait_for_running_condition(client: RunClient):
    with Printer.console.status("Waiting for running condition ...") as live_update:
        try:
            _wait_for_running_condition(client, live_update)
        except (ApiException, HTTPError) as e:
            handle_cli_error(
                e,
                message="Could not wait for running condition "
                "for run `{}` under project `{}/{}`.".format(
                    client.run_uuid, client.owner, client.project
                ),
            )
            sys.exit(1)
