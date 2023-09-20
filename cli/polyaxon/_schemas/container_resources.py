from typing import Dict, List, Optional

from clipped.compact.pydantic import StrictInt, StrictStr
from clipped.types.numbers import StrictIntOrFloat
from clipped.types.uuids import UUIDStr

from polyaxon._schemas.base import BaseSchemaModel


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
