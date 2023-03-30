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
from typing import Dict, List, Optional

from pydantic import StrictInt, StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.fields import StrictIntOrFloat, UUIDStr


class ContainerGPUResourcesConfig(BaseSchemaModel):
    _IDENTIFIER = "ContainerGPUResources"
    _MEM_SIZE_ATTRIBUTES = ["memory_free", "memory_used", "memory_total"]

    index: StrictInt
    uuid: UUIDStr
    name: StrictStr
    minor: StrictInt
    bus_id: StrictStr
    serial: StrictStr
    temperature_gpu: StrictIntOrFloat
    utilization_gpu: StrictIntOrFloat
    power_draw: StrictIntOrFloat
    power_limit: StrictIntOrFloat
    memory_free: StrictIntOrFloat
    memory_used: StrictIntOrFloat
    memory_total: StrictIntOrFloat
    memory_utilization: StrictIntOrFloat
    processes: Optional[List[Dict]]


class ContainerResourcesConfig(BaseSchemaModel):
    _IDENTIFIER = "ContainerResources"
    _PERCENT_ATTRIBUTES = ["cpu_percentage"]
    _MEM_SIZE_ATTRIBUTES = ["memory_used", "memory_limit"]

    job_uuid: UUIDStr
    experiment_uuid: UUIDStr
    job_name: StrictStr
    container_id: StrictStr
    n_cpus: StrictIntOrFloat
    cpu_percentage: StrictIntOrFloat
    percpu_percentage: Optional[List[float]]
    memory_used: StrictIntOrFloat
    memory_limit: StrictIntOrFloat
    gpu_resources: Optional[List[ContainerGPUResourcesConfig]]
