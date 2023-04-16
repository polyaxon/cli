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
from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.types.ref_or_obj import RefField
from pydantic import Field, PositiveInt, validator

from polyaxon.polyflow.early_stopping import V1EarlyStopping
from polyaxon.polyflow.matrix.base import BaseSearchConfig
from polyaxon.polyflow.matrix.kinds import V1MatrixKind


class V1Mapping(BaseSearchConfig):
    """Mapping is a flexible way for dynamically executing a component sequentially or in parallel
    based on a list of parameter combinations.

    Args:
        kind: str, should be equal `mapping`
        values: List[Dict]
        concurrency: int, optional
        early_stopping: List[[EarlyStopping](/docs/automation/helpers/early-stopping)], optional

    ## YAML usage

    ```yaml
    >>> matrix:
    >>>   kind: mapping
    >>>   values:
    >>>   concurrency:
    >>>   earlyStopping:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.polyflow import V1Mapping, V1FailureEarlyStopping
    >>> mapping = V1Mapping(
    >>>     values=[{...}, {...}, ...],
    >>>     concurrency=4,
    >>>     early_stopping=[V1FailureEarlyStopping(...)]
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this matrix is mapping.

    If you are using the python client to create the mapping,
    this field is not required and is set by default.

    ```yaml
    >>> matrix:
    >>>   kind: mapping
    ```

    ### values

    A List of dictionaries (key/value objects) that will be used to pass
    those dictionaries as params to each execution.

    ```yaml
    >>> matrix:
    >>>   values:
    >>>     - lr: 0.001
    >>>       dropout: 0.1
    >>>     - lr: 0.01
    >>>       dropout: 0.2
    >>>     - lr: 0.1
    >>>       dropout: 0.3
    ```

    ### concurrency

    An optional value to set the number of concurrent operations.

    <blockquote class="light">
    This value only makes sense if less or equal to the total number of possible runs.
    </blockquote>

    ```yaml
    >>> matrix:
    >>>   concurrency: 2
    ```

    For more details about concurrency management,
    please check the [concurrency section](/docs/automation/helpers/concurrency/).

    ### earlyStopping

    A list of early stopping conditions to check for terminating
    all operations managed by the pipeline.
    If one of the early stopping conditions is met,
    a signal will be sent to terminate all running and pending operations.

    ```yaml
    >>> matrix:
    >>>   earlyStopping: ...
    ```

    For more details please check the
    [early stopping section](/docs/automation/helpers/early-stopping/).
    """

    _IDENTIFIER = V1MatrixKind.MAPPING

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    values: List[Union[Dict, RefField]]
    concurrency: Optional[Union[PositiveInt, RefField]]
    early_stopping: Optional[Union[List[V1EarlyStopping], RefField]] = Field(
        alias="earlyStopping"
    )

    @validator("concurrency")
    def check_concurrency(cls, v):
        if v and v < 1:
            raise ValueError(
                f"concurrency must be greater than 1, received `{v} instead."
            )
        return v

    def has_key(self, key: str):
        return self.values and key in set(self.values[0].keys())
