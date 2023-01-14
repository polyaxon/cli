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

# pylint:disable=inconsistent-return-statements
import functools
import warnings

from typing import Tuple

from polyaxon.utils.versions import compare_versions


class DeprecatedWarning(DeprecationWarning):
    def __init__(self, message, details: str = None):
        self.message = message
        self.details = details
        super(DeprecatedWarning, self).__init__(message, details)

    def __str__(self):
        return "%s\n%s" % (self.message, self.details)


class UnsupportedWarning(DeprecatedWarning):
    pass


def check_deprecation(
    current_version: str = None,
    deprecation_version: str = None,
    latest_version: str = None,
) -> Tuple[bool, bool]:
    if deprecation_version is None and latest_version is not None:
        raise TypeError(
            "Cannot set `latest_version` to a value without also setting `deprecation_version`"
        )

    is_deprecated = False
    is_unsupported = False

    if current_version:
        if latest_version and compare_versions(current_version, latest_version, ">="):
            is_unsupported = True
        elif deprecation_version and compare_versions(
            current_version, deprecation_version, ">="
        ):
            is_deprecated = True
    else:
        # Automatically deprecate based if only deprecation version is provided.
        is_deprecated = True

    return is_deprecated, is_unsupported


def get_deprecation_warning_message(
    deprecation_version: str,
    latest_version: str,
    current_logic: str,
    new_logic: str = None,
) -> str:
    message = [f"`{current_logic}` is deprecated as of `{deprecation_version}`"]
    if latest_version:
        message.append(f"it will be removed in `{latest_version}`")
    if new_logic:
        message.append(f"please use `{new_logic}` instead")
    return ", ".join(message) + "."


def warn_deprecation(
    deprecation_version: str = None,
    latest_version: str = None,
    current_version: str = None,
    current_logic: str = None,
    new_logic: str = None,
    details: str = None,
):
    is_deprecated, is_unsupported = check_deprecation(
        current_version=current_version,
        deprecation_version=deprecation_version,
        latest_version=latest_version,
    )

    if is_deprecated or is_unsupported:
        if is_unsupported:
            cls = UnsupportedWarning
        else:
            cls = DeprecatedWarning

        message = get_deprecation_warning_message(
            deprecation_version=deprecation_version,
            latest_version=latest_version,
            current_logic=current_logic,
            new_logic=new_logic,
        )
        warnings.warn(cls(message, details), category=DeprecationWarning, stacklevel=2)


def deprecated(
    deprecation_version: str = None,
    latest_version: str = None,
    current_version: str = None,
    current_logic: str = None,
    new_logic: str = None,
    details: str = None,
):
    """This decorator can be used to warn about deprecated functions.

    Example:
        # Class function
        class MyClass:
            @deprecated(deprecation_version=..., ...)
            def foo(self, a, b):
                ...

        # Function with other decorators
        @other_decorators_must_be_upper
        @deprecated(deprecation_version=..., ...)
        def my_func():
            pass
    """

    def wrapper(func):
        @functools.wraps(func)
        def _inner(*args, **kwargs):
            _current_logic = (
                current_logic
                or "The function `%(name)s` in file `%(filename)s` "
                "line number `%(line)s` is deprecated."
                % {
                    "name": func.__name__,
                    "filename": func.__code__.co_filename,
                    "line": func.__code__.co_firstlineno + 1,
                }
            )
            warn_deprecation(
                current_version=current_version,
                deprecation_version=deprecation_version,
                latest_version=latest_version,
                current_logic=_current_logic,
                new_logic=new_logic,
                details=details,
            )
            return func(*args, **kwargs)

        return _inner

    return wrapper
