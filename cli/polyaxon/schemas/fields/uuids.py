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

from uuid import UUID

from pydantic import StrictStr


class UUIDStr(StrictStr):
    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def validate(cls, value, **kwargs):
        if isinstance(value, str):
            return UUID(value).hex
        if isinstance(value, UUID):
            return value.hex
        if not value:
            return value

        field = kwargs.get("field")
        raise TypeError(
            f"Field `{field.name}` value be a valid UUID, received `{value}` instead."
        )
