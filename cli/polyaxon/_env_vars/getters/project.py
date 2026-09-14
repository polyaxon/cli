import sys
from typing import NamedTuple, Optional

from clipped.formatting import Printer
from clipped.utils.strings import validate_slug
from polyaxon._constants.globals import DEFAULT
from polyaxon._env_vars.getters._context import (
    _ContextSource,
    _get_cache_source,
)
from polyaxon._env_vars.getters.user import _get_local_owner_context
from polyaxon._managers.project import ProjectConfigManager
from polyaxon._utils.cache import get_local_project
from polyaxon._utils.fqn_utils import (
    get_entity_info,
    get_owner_team_space,
    split_owner_team_space,
)
from polyaxon.exceptions import PolyaxonClientException, PolyaxonSchemaError
from polyaxon.logger import logger


class _ProjectContext(NamedTuple):
    owner: Optional[str]
    team: Optional[str]
    project: Optional[str]
    owner_source: _ContextSource = _ContextSource()
    project_source: _ContextSource = _ContextSource()

    def fields(self):
        return [
            ("Owner", get_owner_team_space(self.owner, self.team), self.owner_source),
            ("Project", self.project, self.project_source),
        ]

    def report(self):
        owner = get_owner_team_space(self.owner, self.team)
        if self.owner_source.path and self.owner_source != self.project_source:
            logger.info(
                f"Using cached owner `{owner}` from `{self.owner_source.path}`."
            )
        if self.project_source.path:
            cached_project = (
                f"{owner}/{self.project}"
                if self.owner_source == self.project_source
                else self.project
            )
            logger.info(
                f"Using cached project `{cached_project}` "
                f"from `{self.project_source.path}`."
            )


def get_project_error_message(owner, project):
    if not owner or not project:
        return (
            "Please provide a valid project. "
            "Context: <owner: {}> - <project: {}>".format(
                owner or "Missing", project or "Missing"
            )
        )


def _get_project_context(project=None, is_cli: bool = False) -> _ProjectContext:
    from polyaxon import settings

    if not project and not ProjectConfigManager.is_initialized():
        error_message = "Please provide a valid project or initialize a project in the current path."
        if is_cli:
            Printer.error(error_message)
            sys.exit(1)
        else:
            raise PolyaxonClientException(error_message)

    owner_source = project_source = _ContextSource()
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
        owner_source = project_source = _get_cache_source(ProjectConfigManager)

    if not owner:
        owner, owner_source = _get_local_owner_context(is_cli=is_cli)

    if not owner and (not settings.CLI_CONFIG or settings.CLI_CONFIG.is_community):
        owner = DEFAULT
        owner_source = _ContextSource("default")

    owner, team = split_owner_team_space(owner)

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
    return _ProjectContext(owner, team, project_name, owner_source, project_source)
