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
from typing import List, Optional, Union

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.fields.ref_or_obj import BoolOrRef, IntOrRef, RefField
from polyaxon.utils.enums_utils import PEnum


class V1Cache(BaseSchemaModel):
    """Polyaxon provides a caching layer for operation executions,
    this behavior is enabled by default for all runs executed in the context of a DAG,
    a hyperparameter tuning, or a mapping.

    When runs are cached their outputs will be reused for future
    runs with similar inputs and component version.

    Args:
        disable: bool, optional, default: False
        ttl: int, optional
        io: List[str], optional
        sections: List[str], optional

    ## YAML usage

    ```yaml
    >>> cache:
    >>>   disable:
    >>>   ttl:
    >>>   inputs:
    >>>   sections:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.polyflow import V1Cache
    >>> cache = V1Cache(
    >>>   disable=False,
    >>>   ttl=3600,
    >>>   io=['param1', 'param4']
    >>>   sections=['init']
    >>> )
    ```

    ## Fields

    ### disable

    Caching is enabled by default, if you want to disable the cache
    for a component or just for a specific component run, you can set this field to `false`

    ```yaml
    >>> cache:
    >>>   disable: true
    ```

    ### ttl

    the default caching behavior is to persist and reuse a run's results everytime a new operation
    with similar characteristics is scheduled to run.

    In order to invalidate the cache after a certain period of time you can
    define a time to live value.

    ```yaml
    >>> cache:
    >>>   ttl: 36000  # 10 hours
    ```

    ### io

    You may want to discard an input/output from being considered for
    the cache state calculation,
    or you may want to cache a component's run irrespective of the params you pass to some io.

    This field gives you full control to define how you want to calculate the cache state.

    ```yaml
    >>> cache:
    >>>   io: ['param1', 'param4']
    ```

    ### sections

    By default the cache manager will consider the state of the `init`, `connections`,
    and `containers` (command and args) to trigger the cache hit logic.
    You may want to discard a section from being considered for
    the cache state calculation.

    This field gives you allows to define the sections that should be used
    to calculate the cache state.

    ```yaml
    >>> cache:
    >>>   sections: ['containers']
    ```
    """

    _IDENTIFIER = "cache"

    class CacheSections(str, PEnum):
        CONTAINERS = "containers"
        INIT = "init"
        CONNECTIONS = "connections"

    disable: Optional[BoolOrRef]
    ttl: Optional[IntOrRef]
    io: Optional[Union[List[StrictStr], RefField]]
    sections: Optional[Union[List[CacheSections], RefField]]
