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
from typing import Union
from typing_extensions import Annotated

from pydantic import Field

from polyaxon.polyflow.early_stopping.policies import (
    V1DiffStoppingPolicy,
    V1FailureEarlyStopping,
    V1MedianStoppingPolicy,
    V1MetricEarlyStopping,
    V1TruncationStoppingPolicy,
)

V1EarlyStopping = Annotated[
    Union[V1MetricEarlyStopping, V1FailureEarlyStopping],
    Field(discriminator="kind", alias="earlyStopping"),
]
