import logging
import os
import sys

from functools import wraps
from typing import List, Union

from polyaxon._env_vars.keys import ENV_KEYS_DEBUG, ENV_KEYS_LOG_LEVEL

logger = logging.getLogger("polyaxon.cli")


def configure_logger(verbose):
    # DO NOT MOVE OUTSIDE THE FUNCTION!
    from polyaxon import settings
    from polyaxon._plugins.sentry import set_raven_client

    if verbose or settings.CLIENT_CONFIG.debug or os.environ.get(ENV_KEYS_DEBUG, False):
        log_level = logging.DEBUG
        os.environ[ENV_KEYS_LOG_LEVEL] = "DEBUG"
        settings.CLIENT_CONFIG.debug = True
    else:
        if not settings.CLIENT_CONFIG.disable_errors_reporting:
            set_raven_client()
        log_level = (
            logging.DEBUG
            if os.environ.get(ENV_KEYS_LOG_LEVEL) in ["debug", "DEBUG"]
            else logging.INFO
        )
        if settings.CLIENT_CONFIG.log_level:
            try:
                log_level = logging.getLevelName(
                    settings.CLIENT_CONFIG.log_level.upper()
                )
            except Exception:  # noqa
                pass
    logging.basicConfig(format="%(message)s", level=log_level, stream=sys.stdout)


def clean_outputs(fn):
    """Decorator for CLI with Sentry client handling.
    see https://github.com/getsentry/sentry-python/issues/862#issuecomment-712697356
    """

    @wraps(fn)
    def clean_outputs_wrapper(*args, **kwargs):
        from polyaxon import settings

        cli_config = settings.CLI_CONFIG
        if cli_config and cli_config.log_handler and cli_config.log_handler.dsn:
            import sentry_sdk

            try:
                sentry_sdk.flush()
                return fn(*args, **kwargs)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                sentry_sdk.flush()
                raise e
            finally:
                sentry_sdk.flush()
        else:
            return fn(*args, **kwargs)

    return clean_outputs_wrapper


def reconfigure_loggers(
    logger_names: List[str],
    log_level: Union[int, str] = logging.WARNING,
    disable: bool = True,
):
    for logger_name in logger_names:
        logging.getLogger(logger_name).setLevel(log_level)
        if disable:
            logging.getLogger(logger_name).disabled = True
