import os
from typing import NamedTuple, Optional

import click

from clipped.formatting import Printer
from clipped.utils.bools import to_bool
from polyaxon._env_vars.getters._context import (
    _ContextSource,
    _get_cache_source,
)
from polyaxon._env_vars.getters.project import _get_project_context, _ProjectContext
from polyaxon._env_vars.keys import (
    ENV_KEYS_COLLECT_ARTIFACTS,
    ENV_KEYS_COLLECT_RESOURCES,
    ENV_KEYS_RUN_INSTANCE,
)
from polyaxon._utils.fqn_utils import get_owner_team_space, split_owner_team_space
from polyaxon.exceptions import PolyaxonClientException
from polyaxon.logger import logger


class _RunContext(NamedTuple):
    uuid: Optional[str]
    owner: Optional[str] = None
    project: Optional[str] = None
    source: _ContextSource = _ContextSource()

    @property
    def path(self) -> Optional[str]:
        return self.source.path

    @property
    def incomplete(self) -> bool:
        return bool(self.path and self.uuid and (not self.owner or not self.project))

    def report(self):
        if not self.path or not self.uuid:
            return

        message = f"Using cached run `{self.uuid}` from `{self.path}`."
        if self.incomplete:
            message += (
                " Cached owner/project metadata is incomplete; "
                "only known ownership fields were checked."
            )
        log_notice = logger.warning if self.incomplete else logger.info
        log_notice(message)

    def validate(self, project_context: _ProjectContext):
        if not self.path or not self.uuid:
            return

        cached_owner, _ = split_owner_team_space(self.owner)
        owner, _ = split_owner_team_space(project_context.owner)
        project = project_context.project
        if (cached_owner and owner and cached_owner != owner) or (
            self.project and project and self.project != project
        ):
            raise PolyaxonClientException(
                "Cached run `{}/{}/{}` ({}) conflicts with project `{}/{}` "
                "(owner: {}; project: {}). "
                "Provide both `--project OWNER/PROJECT` and `--uid UUID` in the CLI, "
                "or `owner`, `project`, and `run_uuid` in the Python client.".format(
                    self.owner or "unknown",
                    self.project or "unknown",
                    self.uuid,
                    self.source.describe(),
                    get_owner_team_space(owner, project_context.team),
                    project,
                    project_context.owner_source.describe(),
                    project_context.project_source.describe(),
                )
            )


def _get_run_context(run_uuid=None, is_cli: bool = False) -> _RunContext:
    from polyaxon._managers.run import RunConfigManager

    if run_uuid:
        return _RunContext(uuid=run_uuid)
    if is_cli:
        run = RunConfigManager.get_config_or_raise()
    else:
        try:
            run = RunConfigManager.get_config()
        except TypeError:
            Printer.error(
                "Found an invalid run config or run config cache, "
                "if you are using Polyaxon CLI please run: "
                "`polyaxon config purge --cache-only`",
                sys_exit=True,
            )
    if run:
        return _RunContext(
            uuid=run.uuid,
            owner=run.owner,
            project=run.project,
            source=_get_cache_source(RunConfigManager),
        )
    return _RunContext(uuid=None)


def get_run_or_local(run_uuid=None, is_cli: bool = False):
    return _get_run_context(run_uuid, is_cli=is_cli).uuid


def _get_project_run_context(project=None, run_uuid=None, is_cli: bool = True):
    project_context = _get_project_context(project, is_cli=is_cli)
    context = _get_run_context(run_uuid, is_cli=is_cli)
    try:
        context.validate(project_context)
    except PolyaxonClientException as e:
        if is_cli:
            raise click.ClickException(str(e)) from e
        raise
    return project_context, context


def get_collect_artifacts(arg: Optional[bool] = None, default: Optional[bool] = None):
    """If set, Polyaxon will collect artifacts"""
    return (
        arg
        if arg is not None
        else to_bool(os.getenv(ENV_KEYS_COLLECT_ARTIFACTS, default), handle_none=True)
    )


def get_collect_resources(arg: Optional[bool] = None, default: Optional[bool] = None):
    """If set, Polyaxon will collect resources"""
    return (
        arg
        if arg is not None
        else to_bool(os.getenv(ENV_KEYS_COLLECT_RESOURCES, default), handle_none=True)
    )


def get_log_level():
    """If set on the polyaxonfile it will return the log level."""
    from polyaxon import settings

    return settings.CLIENT_CONFIG.log_level


def get_run_info(run_instance: Optional[str] = None):
    run_instance = run_instance or os.getenv(ENV_KEYS_RUN_INSTANCE, None)
    if not run_instance:
        raise PolyaxonClientException(
            "Could not get run info, "
            "please make sure this is run is correctly started by Polyaxon."
        )
    return get_run_info_from_instance(run_instance)


def get_run_info_from_instance(run_instance: str):
    parts = run_instance.split(".")
    if not len(parts) == 4:
        raise PolyaxonClientException(
            "run instance is invalid `{}`, "
            "please make sure this is run is correctly started by Polyaxon.".format(
                run_instance
            )
        )
    return parts[0], parts[1], parts[-1]
