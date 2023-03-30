#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import functools

from urllib3.exceptions import HTTPError

from polyaxon import settings
from polyaxon.client import PolyaxonClient
from polyaxon.client.decorators.errors import handle_client_error
from polyaxon.logger import logger
from polyaxon.sdk.exceptions import ApiException


def client_handler(
    check_no_op: bool = True,
    check_offline: bool = False,
    can_log_events: bool = False,
    can_log_outputs: bool = False,
):
    """
    The `ClientHandlerDecorator` is a decorator to handle several checks in PolyaxonClient.

     * check_offline: to ignore any decorated function when POLYAXON_IS_OFFLINE env var is found.
     * check_no_op: to ignore any decorated function when NO_OP env var is found.
     * handle_openapi_exceptions: to handle exception of OpenApi and generate better
        debugging outputs.
     * can_log_events: to check if there's an event logger instance on the object.
     * can_log_outputs: to check if there's an outputs path set on the run.
     * openapi_extra_context: to augment openapi errors.

    usage example with class method:
        @client_handler(check_no_op=True)
        def my_func(self, *args, **kwargs):
            ...
            return ...

    usage example with a function:
        @client_handler(check_no_op=True)
        def my_func(arg1, arg2):
            ...
            return ...
    """

    def _check_global_or_inline_config(args, config_key):
        self_arg = args[0] if args else None
        config_value = getattr(self_arg, f"_{config_key}", None)
        return get_global_or_inline_config(
            config_key=config_key,
            config_value=config_value,
            client=getattr(self_arg, "_client", None),
        )

    def client_handler_wrapper(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if check_no_op and _check_global_or_inline_config(args, "no_op"):
                logger.debug("Using NO_OP mode")
                return None
            if check_offline and _check_global_or_inline_config(args, "is_offline"):
                logger.debug("Using IS_OFFLINE mode")
                return None
            manual_exceptions_handling = False
            if args:
                self_arg = args[0]

                manual_exceptions_handling = getattr(
                    self_arg, "_manual_exceptions_handling", False
                )

                if can_log_events and (
                    not hasattr(self_arg, "_event_logger")
                    or self_arg._event_logger is None  # pylint:disable=protected-access
                ):
                    logger.warning(
                        "You should set an event logger before calling: {}".format(
                            f.__name__
                        )
                    )

                if can_log_outputs and (
                    not hasattr(self_arg, "_outputs_path")
                    or self_arg._outputs_path is None  # pylint:disable=protected-access
                ):
                    logger.warning(
                        "You should set an an outputs path before calling: {}".format(
                            f.__name__
                        )
                    )

            try:
                return f(*args, **kwargs)
            except (ApiException, HTTPError) as e:
                message = (
                    "\nAPI Client failed at the function `%(name)s` in file "
                    "`%(filename)s` line number `%(line)s`."
                    "\nClient config:\n%(config)s\n"
                    % {
                        "name": f.__name__,
                        "filename": f.__code__.co_filename,
                        "line": f.__code__.co_firstlineno + 1,
                        "config": settings.CLIENT_CONFIG.to_dict(),
                    }
                )
                handle_client_error(
                    e=None if manual_exceptions_handling else e, message=message
                )
                if manual_exceptions_handling:
                    raise e

        return wrapper

    return client_handler_wrapper


def get_global_or_inline_config(
    config_key: str,
    config_value: bool = None,
    client: PolyaxonClient = None,
):
    if config_value is not None:
        return config_value
    if client and client.config and getattr(client.config, config_key) is not None:
        return getattr(client.config, config_key)
    return getattr(settings.CLIENT_CONFIG, config_key, None)
