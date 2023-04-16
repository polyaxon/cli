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

from typing import Optional

from clipped.config.schema import skip_partial
from pydantic import Field, StrictInt, StrictStr, root_validator

from polyaxon.schemas.base import BaseSchemaModel


def validate_security_context(user, group):
    if any([user, group]) and not all([user, group]):
        raise ValueError("Security context requires both `user` and `group` or none.")


class SecurityContextConfig(BaseSchemaModel):
    enabled: Optional[bool]
    run_as_user: Optional[StrictInt] = Field(alias="runAsUser")
    run_as_group: Optional[StrictInt] = Field(alias="runAsGroup")
    fs_group: Optional[StrictInt] = Field(alias="fsGroup")
    fs_group_change_policy: Optional[StrictStr] = Field(alias="fsGroupChangePolicy")
    allow_privilege_escalation: Optional[bool] = Field(alias="allowPrivilegeEscalation")
    run_as_non_root: Optional[bool] = Field(alias="runAsNonRoot")

    @root_validator
    @skip_partial
    def validate_security_context(cls, values):
        validate_security_context(values.get("run_as_user"), values.get("run_as_group"))
        return values
