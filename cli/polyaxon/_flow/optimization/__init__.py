from typing import Optional

from clipped.compact.pydantic import StrictStr

from polyaxon._flow.optimization.enums import V1Optimization, V1ResourceType
from polyaxon._schemas.base import BaseSchemaModel


class V1OptimizationMetric(BaseSchemaModel):
    _IDENTIFIER = "optimization_metric"

    name: StrictStr
    optimization: Optional[V1Optimization]

    def get_for_sort(self):
        if self.optimization == V1Optimization.MINIMIZE:
            return self.name
        return "-{}".format(self.name)


class V1OptimizationResource(BaseSchemaModel):
    _IDENTIFIER = "optimization_resource"

    name: StrictStr
    type: Optional[V1ResourceType]

    def cast_value(self, value):
        if V1ResourceType.is_int(self.type):
            return int(value)
        if V1ResourceType.is_float(self.type):
            return float(value)
        return value
