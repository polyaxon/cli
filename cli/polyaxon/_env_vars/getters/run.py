import os

from typing import Optional

from clipped.formatting import Printer
from clipped.utils.bools import to_bool

from polyaxon._env_vars.getters.project import get_project_or_local
from polyaxon._env_vars.keys import (
    ENV_KEYS_COLLECT_ARTIFACTS,
    ENV_KEYS_COLLECT_RESOURCES,
    ENV_KEYS_RUN_INSTANCE,
)
from polyaxon.exceptions import PolyaxonClientException


def get_run_or_local(run_uuid=None, is_cli: bool = False):
    from polyaxon._managers.run import RunConfigManager

    if run_uuid:
        return run_uuid
    if is_cli:
        return RunConfigManager.get_config_or_raise().uuid

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
        return run.uuid
    return None


def get_project_run_or_local(project=None, run_uuid=None, is_cli: bool = True):
    user, project_name = get_project_or_local(project, is_cli=is_cli)
    run_uuid = get_run_or_local(run_uuid, is_cli=is_cli)
    return user, project_name, run_uuid


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
