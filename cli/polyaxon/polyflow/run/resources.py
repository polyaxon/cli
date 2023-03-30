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
from typing import Optional, Union

from pydantic import StrictStr

from polyaxon.k8s.k8s_schemas import V1Container
from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.fields import StrictIntOrFloat
from traceml.processors.units_processors import to_cpu_value, to_memory_bytes


class V1RunResources(BaseSchemaModel):
    cpu: Optional[Union[StrictIntOrFloat, StrictStr]]
    memory: Optional[Union[StrictIntOrFloat, StrictStr]]
    gpu: Optional[Union[StrictIntOrFloat, StrictStr]]
    custom: Optional[Union[StrictIntOrFloat, StrictStr]]
    cost: Optional[Union[StrictIntOrFloat, StrictStr]]

    _MEMORY = "memory"
    _CPU = "cpu"
    _GPU = "gpu"
    _CUSTOM_RESOURCE = "custom"
    _COST = "cost"
    _VALUES = {_MEMORY, _CPU, _GPU, _CUSTOM_RESOURCE, _COST}

    @classmethod
    def validate_memory(cls, value):
        return to_memory_bytes(value or 0)

    @classmethod
    def validate_cpu(cls, value):
        return to_cpu_value(value or 0)

    @classmethod
    def validate_resource(cls, value):
        try:
            return float(value or 0)
        except (ValueError, TypeError):
            return 0

    @classmethod
    def from_container(cls, container: V1Container):
        result = cls(memory=0, cpu=0, gpu=0, custom=0, cost=0)
        if not container or not container.resources:
            return result

        resources = container.resources
        if hasattr(resources, "to_dict"):
            resources = resources.to_dict()

        requests = resources.get("requests") or {}
        limits = resources.get("limits") or {}

        for k, v in requests.items():
            if k == cls._MEMORY:
                result.memory = v
            elif k == cls._CPU:
                result.cpu = v
            elif cls._GPU in k:
                result.gpu = v
            else:
                result.custom = v
        # We only set limits if no requests is provided
        for k, v in limits.items():
            if k == cls._MEMORY:
                result.memory = result.memory if result.memory else v
            elif k == cls._CPU:
                result.cpu = result.cpu if result.cpu else v
            elif cls._GPU in k:
                result.gpu = result.gpu if result.gpu else v
            elif not result.custom:
                result.custom = v

        # Parse values
        result.memory = cls.validate_memory(result.memory)
        result.cpu = cls.validate_cpu(result.cpu)
        result.gpu = cls.validate_resource(result.gpu)
        result.custom = cls.validate_resource(result.custom)
        return result

    def __add__(self, other):
        if not other:
            return self

        def _get_value(v1, v2):
            return v1 or 0 + v2 or 0

        return V1RunResources(
            memory=_get_value(self.memory, other.memory),
            cpu=_get_value(self.cpu, other.cpu),
            gpu=_get_value(self.gpu, other.gpu),
            custom=_get_value(self.custom, other.custom),
            cost=_get_value(self.cost, other.cost),
        )
