import os
from typing import NamedTuple, Optional

import click

from clipped.formatting import Printer
from clipped.utils.bools import to_bool
from polyaxon._env_vars.getters.project import get_project_or_local
from polyaxon._env_vars.keys import (
    ENV_KEYS_COLLECT_ARTIFACTS,
    ENV_KEYS_COLLECT_RESOURCES,
    ENV_KEYS_RUN_INSTANCE,
)
from polyaxon._utils.fqn_utils import split_owner_team_space
from polyaxon.exceptions import PolyaxonClientException


class _RunContext(NamedTuple):
    uuid: Optional[str]
    owner: Optional[str] = None
    project: Optional[str] = None
    path: Optional[str] = None

    def validate(self, owner: Optional[str], project: Optional[str]):
        if not self.path or not self.uuid:
            return

        cached_owner, _ = split_owner_team_space(self.owner)
        owner, _ = split_owner_team_space(owner)
        if (cached_owner and owner and cached_owner != owner) or (
            self.project and project and self.project != project
        ):
            raise PolyaxonClientException(
                "Cached run `{}/{}/{}` from `{}` conflicts with project `{}/{}`. "
                "Provide both `--project OWNER/PROJECT` and `--uid UUID` in the CLI, "
                "or `owner`, `project`, and `run_uuid` in the Python client.".format(
                    cached_owner or "unknown",
                    self.project or "unknown",
                    self.uuid,
                    self.path,
                    owner,
                    project,
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
            path=os.path.abspath(RunConfigManager.get_config_filepath(create=False)),
        )
    return _RunContext(uuid=None)


def get_run_or_local(run_uuid=None, is_cli: bool = False):
    return _get_run_context(run_uuid, is_cli=is_cli).uuid


def get_project_run_or_local(project=None, run_uuid=None, is_cli: bool = True):
    owner, team, project_name = get_project_or_local(project, is_cli=is_cli)
    context = _get_run_context(run_uuid, is_cli=is_cli)
    try:
        context.validate(owner, project_name)
    except PolyaxonClientException as e:
        if is_cli:
            raise click.ClickException(str(e)) from e
        raise
    return owner, team, project_name, context.uuid


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
