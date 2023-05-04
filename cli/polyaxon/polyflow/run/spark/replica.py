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

from clipped.types.ref_or_obj import RefField
from pydantic import StrictInt, validator

from polyaxon.k8s import k8s_schemas, k8s_validation
from polyaxon.polyflow.environment import V1Environment
from polyaxon.polyflow.init import V1Init
from polyaxon.schemas.base import BaseSchemaModel


class V1SparkReplica(BaseSchemaModel):
    """Spark replica is the specification for a Spark executor or driver.

    Args:
        replicas: str, int
        environment: [V1Environment](/docs/core/specification/environment/), optional
        init: List[[V1Init](/docs/core/specification/init/)], optional
        sidecars: List[[sidecar containers](/docs/core/specification/sidecars/)], optional
        container: [Kubernetes Container](https://kubernetes.io/docs/concepts/containers/)

    ## YAML usage

    ```yaml
    >>> executor/driver:
    >>>   replicas
    >>>   environment:
    >>>   init:
    >>>   sidecars:
    >>>   container:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.polyflow import V1Environment, V1Init, V1SparkReplica
    >>> from polyaxon.k8s import k8s_schemas
    >>> replica = V1SparkReplica(
    >>>     replicas=2,
    >>>     environment=V1Environment(...),
    >>>     init=[V1Init(...)],
    >>>     sidecars=[k8s_schemas.V1Container(...)],
    >>>     container=k8s_schemas.V1Container(...),
    >>> )
    ```

    ## Fields

    ### replicas

    The number of replica (executor/driver) instances.

    ```yaml
    >>> executor:
    >>>   replicas: 2
    ```

    ### environment

    Optional [environment section](/docs/core/specification/environment/),
    it provides a way to inject pod related information into the replica (executor/driver).

    ```yaml
    >>> driver:
    >>>   environment:
    >>>     labels:
    >>>        key1: "label1"
    >>>        key2: "label2"
    >>>      annotations:
    >>>        key1: "value1"
    >>>        key2: "value2"
    >>>      nodeSelector:
    >>>        node_label: node_value
    >>>      ...
    >>>  ...
    ```

    ### init

    A list of [init handlers and containers](/docs/core/specification/init/)
    to resolve for the replica (executor/driver).

    <blockquote class="light">
    If you are referencing a connection it must be configured.
    All referenced connections will be checked:

     * If they are accessible in the context of the project of this run

     * If the user running the operation can have access to those connections
    </blockquote>

    ```yaml
    >>> executor:
    >>>   init:
    >>>     - artifacts:
    >>>         dirs: ["path/on/the/default/artifacts/store"]
    >>>     - connection: gcs-large-datasets
    >>>       artifacts:
    >>>         dirs: ["data"]
    >>>       container:
    >>>         resources:
    >>>           requests:
    >>>             memory: "256Mi"
    >>>             cpu: "500m"
    >>>     - container:
    >>>       name: myapp-container
    >>>       image: busybox:1.28
    >>>       command: ['sh', '-c', 'echo custom init container']
    ```

    ### sidecars


    A list of [sidecar containers](/docs/core/specification/sidecars/)
    that will used as sidecars.

    ```yaml
    >>> driver:
    >>>   sidecars:
    >>>     - name: sidecar2
    >>>       image: busybox:1.28
    >>>       command: ['sh', '-c', 'echo sidecar2']
    >>>     - name: sidecar1
    >>>       image: busybox:1.28
    >>>       command: ['sh', '-c', 'echo sidecar1']
    >>>       resources:
    >>>         requests:
    >>>           memory: "128Mi"
    >>>           cpu: "500m"
    ```

    ### container

    The [main Kubernetes Container](https://kubernetes.io/docs/concepts/containers/)
    that will run your experiment training or data processing
    logic for the replica (executor/driver).

    ```yaml
    >>> executor:
    >>>   init:
    >>>     - connection: my-code-repo
    >>>   container:
    >>>     name: tensorflow:2.1
    >>>     command: ["python", "/plx-context/artifacts/my-code-repo/model.py"]
    ```
    """

    _IDENTIFIER = "replica"
    _SWAGGER_FIELDS = ["sidecars", "container"]

    replicas: Optional[StrictInt]
    environment: Optional[Union[V1Environment, RefField]]
    init: Optional[Union[List[V1Init], RefField]]
    sidecars: Optional[Union[List[k8s_schemas.V1Container], RefField]]
    container: Optional[Union[k8s_schemas.V1Container, RefField]]

    @validator("sidecars", always=True, pre=True)
    def validate_helper_containers(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_container(vi) for vi in v]

    @validator("container", always=True, pre=True)
    def validate_container(cls, v):
        return k8s_validation.validate_k8s_container(v)
