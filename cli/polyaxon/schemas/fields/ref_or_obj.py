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
from datetime import datetime, timedelta
from typing import Union

from pydantic import StrictFloat, StrictInt, StrictStr
from pydantic.validators import strict_str_validator

from polyaxon.contexts.params import PARAM_REGEX


class RefField(StrictStr):
    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield strict_str_validator
        yield cls.validate

    @classmethod
    def validate(cls, value, **kwargs):
        if not isinstance(value, str):
            return value

        field = kwargs.get("field")
        param = PARAM_REGEX.search(value)
        if not param:  # TODO: Fix error message
            raise ValueError(
                f"Field `{field.name}` value must be equal to `{field.default}`, received `{value}` instead."
            )
        return value


BoolOrRef = Union[bool, RefField]
IntOrRef = Union[StrictInt, RefField]
StrictFloatOrRef = Union[StrictFloat, RefField]
FloatOrRef = Union[float, RefField]
DatetimeOrRef = Union[datetime, RefField]
TimeDeltaOrRef = Union[timedelta, RefField]
