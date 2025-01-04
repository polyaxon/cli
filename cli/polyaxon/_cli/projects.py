import sys

import click

from clipped.formatting import Printer
from clipped.utils.dicts import list_dicts_to_tabulate
from clipped.utils.responses import get_meta_response
from clipped.utils.validation import validate_tags
from urllib3.exceptions import HTTPError

from polyaxon._cli.dashboard import get_dashboard_url, get_project_subpath_url
from polyaxon._cli.errors import handle_cli_error
from polyaxon._cli.init import init as init_project
from polyaxon._cli.options import OPTIONS_NAME, OPTIONS_OWNER, OPTIONS_PROJECT
from polyaxon._cli.utils import get_entity_details
from polyaxon._env_vars.getters import get_project_or_local
from polyaxon._env_vars.getters.owner_entity import resolve_entity_info
from polyaxon._env_vars.getters.user import get_local_owner
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._utils import cache
from polyaxon._utils.cache import get_local_project
from polyaxon._utils.fqn_utils import get_owner_team_space
from polyaxon.client import ProjectClient, V1Project
from polyaxon.exceptions import ApiException
from polyaxon.logger import clean_outputs


@click.group()
@click.option(*OPTIONS_PROJECT["args"], "_project", **OPTIONS_PROJECT["kwargs"])
@click.pass_context
@clean_outputs
def project(ctx, _project):  # pylint:disable=redefined-outer-name
    """Commands for projects."""
    if _project:
        Printer.warning(
            "Passing arguments to command groups is deprecated and will be removed in v2! "
            "Please use arguments on the sub-command directly: "
            "`polyaxon project SUB_COMMAND --help`"
        )
    if ctx.invoked_subcommand not in ["create", "ls"]:
        ctx.obj = ctx.obj or {}
        ctx.obj["project"] = _project


@project.command()
@click.option(
    *OPTIONS_NAME["args"],
    type=str,
    help="The project name, e.g. 'mnist' or 'acme/mnist'.",
)
@click.option("--description", type=str, help="Description of the project.")
@click.option("--tags", type=str, help="Tags of the project (comma separated values).")
@click.option(
    "--public", is_flag=True, help="Set the visibility of the project to public."
)
@click.option("--init", is_flag=True, help="Initialize the project after creation.")
@click.pass_context
@clean_outputs
def create(ctx, name, description, tags, public, init):
    """Create a new project.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon project create --name=cats-vs-dogs --description="Image Classification with DL"

    \b
    $ polyaxon project create --name=owner/name --description="Project Description"
    """
    if not name:
        Printer.error(
            "Please provide a valid name to create a project.",
            command_help="project create",
            sys_exit=True,
        )
    owner, team, project_name = resolve_entity_info(
        name or ctx.obj.get("project"), is_cli=True, entity_name="project"
    )

    tags = validate_tags(tags, validate_yaml=True)

    if not owner:
        Printer.error(
            "Please provide a valid name with an owner namespace: --name=owner/project."
        )
        sys.exit(1)

    try:
        project_config = V1Project(
            name=project_name, description=description, tags=tags, is_public=public
        )
        polyaxon_client = ProjectClient(
            owner=get_owner_team_space(owner, team), manual_exceptions_handling=True
        )
        _project = polyaxon_client.create(project_config)
        config = polyaxon_client.client.sanitize_for_serialization(_project)
        cache.cache(config_manager=ProjectConfigManager, config=config)
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e, message="Could not create project `{}`.".format(project_name)
        )
        sys.exit(1)

    Printer.success("Project `{}` was created successfully.".format(_project.name))
    Printer.print(
        "You can view this project on Polyaxon UI: {}".format(
            get_dashboard_url(
                subpath=get_project_subpath_url(owner, team, _project.name)
            )
        )
    )

    if init:
        ctx.obj = {}
        ctx.invoke(
            init_project,
            project="{}/{}".format(owner, project_name),
            polyaxonignore=True,
        )


@project.command()
@click.option(*OPTIONS_OWNER["args"], **OPTIONS_OWNER["kwargs"])
@click.option(
    "--query", "-q", type=str, help="To filter the projects based on this query spec."
)
@click.option(
    "--sort", "-s", type=str, help="To order the projects based on the sort spec."
)
@click.option("--limit", type=int, help="To limit the list of projects.")
@click.option("--offset", type=int, help="To offset the list of projects.")
@clean_outputs
def ls(owner, query, sort, limit, offset):
    """List projects.

    Uses /docs/core/cli/#caching
    """
    owner = owner or get_local_owner(is_cli=True)
    if not owner:
        Printer.error("Please provide a valid owner: --owner/-o.")
        sys.exit(1)

    try:
        polyaxon_client = ProjectClient(owner=owner, manual_exceptions_handling=True)
        response = polyaxon_client.list(
            limit=limit, offset=offset, query=query, sort=sort
        )
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not get list of projects.")
        sys.exit(1)

    meta = get_meta_response(response)
    if meta:
        Printer.heading("Projects for owner {}".format(owner))
        Printer.heading("Navigation:")
        Printer.dict_tabulate(meta)
    else:
        Printer.heading("No projects found for owner {}".format(owner))

    objects = list_dicts_to_tabulate(
        [o.to_dict() for o in response.results],
        humanize_values=True,
        exclude_attrs=[
            "uuid",
            "readme",
            "description",
            "owner",
            "user_email",
            "role",
            "excluded_features",
            "excluded_runtimes",
            "settings",
        ],
    )
    if objects:
        Printer.heading("Projects:")
        Printer.dict_tabulate(objects, is_list_dict=True)


@project.command()
@click.option(*OPTIONS_PROJECT["args"], "_project", **OPTIONS_PROJECT["kwargs"])
@click.pass_context
@clean_outputs
def get(ctx, _project):
    """Get info for current project, by project_name, or owner/project_name.

    Uses /docs/core/cli/#caching

    Examples:

    To get current project:

    \b
    $ polyaxon project get

    To get a project by name

    \b
    $ polyaxon project get -p owner/project
    """
    owner, team, project_name = get_project_or_local(
        _project or ctx.obj.get("project"), is_cli=True
    )

    try:
        polyaxon_client = ProjectClient(
            owner=owner, project=project_name, manual_exceptions_handling=True
        )
        polyaxon_client.refresh_data()
        config = polyaxon_client.client.sanitize_for_serialization(
            polyaxon_client.project_data
        )
        cache.cache(
            config_manager=ProjectConfigManager,
            config=config,
            owner=owner,
            project=project_name,
        )
        get_entity_details(polyaxon_client.project_data, "Project")
        Printer.print(
            "You can view this project on Polyaxon UI: {}".format(
                get_dashboard_url(
                    subpath=get_project_subpath_url(owner, team, project_name)
                )
            )
        )
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e, message="Could not get project `{}`.".format(project_name), sys_exit=True
        )


@project.command()
@click.option(*OPTIONS_PROJECT["args"], "_project", **OPTIONS_PROJECT["kwargs"])
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
def delete(ctx, _project, yes):
    """Delete project.

    Uses /docs/core/cli/#caching
    """
    owner, _, project_name = get_project_or_local(
        _project or ctx.obj.get("project"), is_cli=True
    )

    if not yes and not click.confirm(
        "Are sure you want to delete project `{}/{}`".format(owner, project_name)
    ):
        Printer.print("Exiting without deleting project.")
        sys.exit(1)

    try:
        polyaxon_client = ProjectClient(
            owner=owner, project=project_name, manual_exceptions_handling=True
        )
        polyaxon_client.delete()
        local_project = get_local_project(is_cli=True)
        if local_project and (owner, project_name) == (
            local_project.owner,
            local_project.name,
        ):
            # Purge caching
            ProjectConfigManager.purge()
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e, message="Could not delete project `{}/{}`.".format(owner, project_name)
        )
        sys.exit(1)

    Printer.success(
        "Project `{}/{}` was delete successfully".format(owner, project_name)
    )


@project.command()
@click.option(*OPTIONS_PROJECT["args"], "_project", **OPTIONS_PROJECT["kwargs"])
@click.option(
    *OPTIONS_NAME["args"],
    type=str,
    help="Name of the project, must be unique for the same user.",
)
@click.option("--description", type=str, help="Description of the project.")
@click.option("--tags", type=str, help="Tags of the project (comma separated values).")
@click.option(
    "--private", type=bool, help="Set the visibility of the project to private/public."
)
@click.pass_context
@clean_outputs
def update(ctx, _project, name, description, tags, private):
    """Update project.

    Uses /docs/core/cli/#caching

    Examples:

    \b
    $ polyaxon project update foobar --description="Image Classification with DL using TensorFlow"

    \b
    $ polyaxon project update mike1/foobar --description="Image Classification with DL using TensorFlow"

    \b
    $ polyaxon update --tags="foo, bar"
    """
    owner, _, project_name = get_project_or_local(
        _project or ctx.obj.get("project"), is_cli=True
    )

    update_dict = {}
    if name:
        update_dict["name"] = name

    if description is not None:
        update_dict["description"] = description

    tags = validate_tags(tags, validate_yaml=True)
    if tags:
        update_dict["tags"] = tags

    if private is not None:
        update_dict["is_public"] = not private

    if not update_dict:
        Printer.warning("No argument was provided to update the project.")
        sys.exit(1)

    try:
        polyaxon_client = ProjectClient(
            owner=owner, project=project_name, manual_exceptions_handling=True
        )
        response = polyaxon_client.update(update_dict)
    except (ApiException, HTTPError) as e:
        handle_cli_error(
            e, message="Could not update project `{}`.".format(project_name)
        )
        sys.exit(1)

    Printer.success("Project updated.")
    get_entity_details(response, "Project")


@project.command()
@click.option(*OPTIONS_PROJECT["args"], "_project", **OPTIONS_PROJECT["kwargs"])
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
    help="Print the url of the dashboard for this project.",
)
@click.pass_context
@clean_outputs
def dashboard(ctx, _project, yes, url):
    """Open this project's dashboard details in browser."""
    owner, team, project_name = get_project_or_local(
        _project or ctx.obj.get("project"), is_cli=True
    )
    project_url = get_dashboard_url(
        subpath=get_project_subpath_url(owner, team, project_name)
    )
    if url:
        Printer.header("The dashboard is available at: {}".format(project_url))
        sys.exit(0)
    if yes or click.confirm(
        "Dashboard page will now open in your browser. Continue?",
        default=True,
    ):
        click.launch(project_url)
