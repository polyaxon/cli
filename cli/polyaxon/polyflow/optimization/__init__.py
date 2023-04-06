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

from clipped.enums_utils import PEnum
from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1ResourceType(str, PEnum):
    INT = "int"
    FLOAT = "float"

    @classmethod
    def init_values(cls):
        return {cls.INT, cls.INT.upper(), cls.INT.capitalize()}

    @classmethod
    def float_values(cls):
        return {cls.FLOAT, cls.FLOAT.upper(), cls.FLOAT.capitalize()}

    @classmethod
    def values(cls):
        return cls.init_values() | cls.float_values()

    @classmethod
    def is_int(cls, value):
        return value in cls.init_values()

    @classmethod
    def is_float(cls, value):
        return value in cls.float_values()


class V1Optimization(str, PEnum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"

    @classmethod
    def maximize_values(cls):
        return [cls.MAXIMIZE, cls.MAXIMIZE.upper(), cls.MAXIMIZE.capitalize()]

    @classmethod
    def minimize_values(cls):
        return [cls.MINIMIZE, cls.MINIMIZE.upper(), cls.MINIMIZE.capitalize()]

    @classmethod
    def maximize(cls, value):
        return value in cls.maximize_values()

    @classmethod
    def minimize(cls, value):
        return value in cls.minimize_values()


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
