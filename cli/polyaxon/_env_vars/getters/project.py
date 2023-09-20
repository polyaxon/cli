import sys

from clipped.formatting import Printer
from clipped.utils.strings import validate_slug

from polyaxon._constants.globals import DEFAULT
from polyaxon._env_vars.getters.user import get_local_owner
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._utils.cache import get_local_project
from polyaxon._utils.fqn_utils import get_entity_info
from polyaxon.exceptions import PolyaxonClientException, PolyaxonSchemaError


def get_project_error_message(owner, project):
    if not owner or not project:
        return (
            "Please provide a valid project. "
            "Context: <owner: {}> - <project: {}>".format(
                owner or "Missing", project or "Missing"
            )
        )


def get_project_or_local(project=None, is_cli: bool = False):
    from polyaxon import settings

    if not project and not ProjectConfigManager.is_initialized():
        error_message = "Please provide a valid project or initialize a project in the current path."
        if is_cli:
            Printer.error(error_message)
            sys.exit(1)
        else:
            raise PolyaxonClientException(error_message)

    if project:
        try:
            owner, project_name = get_entity_info(project)
        except Exception as e:
            if is_cli:
                Printer.error("Please provide a valid project name.\n%s" % e)
                sys.exit(1)
            else:
                raise e
    else:
        project = get_local_project(is_cli=is_cli)

        owner, project_name = project.owner, project.name

    if not owner:
        owner = get_local_owner(is_cli=is_cli)

    if not owner and (not settings.CLI_CONFIG or settings.CLI_CONFIG.is_community):
        owner = DEFAULT

    if not all([owner, project_name]):
        error_message = get_project_error_message(owner, project_name)
        if is_cli:
            Printer.error(error_message)
            sys.exit(1)
        else:
            raise PolyaxonClientException(error_message)

    if owner and not validate_slug(owner):
        error_message = "Received an invalid owner, received the value: `{}`".format(
            owner
        )
        if is_cli:
            Printer.error(error_message)
            sys.exit(1)
        else:
            raise PolyaxonSchemaError(error_message)

    if project_name and not validate_slug(project_name):
        error_message = "Received an invalid project, received the value: `{}`".format(
            project_name
        )
        if is_cli:
            Printer.error(error_message)
            sys.exit(1)
        else:
            raise PolyaxonSchemaError(error_message)
    return owner, project_name
