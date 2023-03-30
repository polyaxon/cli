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

from pydantic import Field, StrictStr

from polyaxon.connections.schemas import V1K8sResourceSchema
from polyaxon.schemas.types.base import BaseTypeConfig


class V1K8sResourceType(BaseTypeConfig):
    _IDENTIFIER = "secret_resource"

    name: StrictStr
    schema_: Optional[V1K8sResourceSchema] = Field(alias="schema")
    is_requested: Optional[bool] = Field(alias="isRequested")

    @classmethod
    def from_model(cls, model, is_requested=False) -> "V1K8sResourceType":
        schema = model.schema_
        if hasattr(schema, "to_dict"):
            schema = schema.to_dict()
        return V1K8sResourceType.from_dict(
            {"name": model.name, "schema": schema, "isRequested": is_requested}
        )
