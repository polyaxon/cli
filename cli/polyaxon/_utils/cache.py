from clipped.formatting import Printer

from polyaxon._managers.project import ProjectConfigManager
from polyaxon.exceptions import PolyaxonSchemaError

CACHE_ERROR = (
    "Found an invalid project config or project config cache, "
    "if you are using Polyaxon CLI please run: "
    "`polyaxon config purge --cache-only`"
)


def get_local_project(is_cli: bool = False):
    try:
        return ProjectConfigManager.get_config()
    except Exception:  # noqa
        if is_cli:
            Printer.error(CACHE_ERROR, sys_exit=True)
        else:
            raise PolyaxonSchemaError(CACHE_ERROR)


def _is_same_project(owner=None, project=None):
    local_project = get_local_project(is_cli=True)
    if project and project == local_project.name:
        return not all([owner, local_project.owner]) or owner == local_project.owner


def _cache_project(config, owner=None, project=None):
    if (
        ProjectConfigManager.is_initialized()
        and ProjectConfigManager.is_locally_initialized()
    ):
        if _is_same_project(owner, project):
            ProjectConfigManager.set_config(config)
            return

    ProjectConfigManager.set_config(
        config, visibility=ProjectConfigManager.Visibility.GLOBAL
    )


def cache(config_manager, config, owner=None, project=None):
    if config_manager == ProjectConfigManager:
        _cache_project(config=config, project=project, owner=owner)

    # Set caching only if we have an initialized project
    if not ProjectConfigManager.is_initialized():
        return

    if not _is_same_project(owner, project):
        return

    visibility = ProjectConfigManager.get_visibility()
    config_manager.set_config(config, visibility=visibility)
