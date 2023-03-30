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
from typing_extensions import Literal

from pydantic import Field, StrictStr, validator

from polyaxon.k8s import k8s_schemas, k8s_validation
from polyaxon.polyflow.environment import V1Environment
from polyaxon.polyflow.init import V1Init
from polyaxon.polyflow.run.base import BaseRun
from polyaxon.polyflow.run.kinds import V1RunKind
from polyaxon.schemas.fields import IntOrRef, RefField


class V1Dask(BaseRun):
    """Dask jobs are used to run distributed jobs using a
    [Dask cluster](https://kubernetes.dask.org/en/latest/).

    > Dask Kubernetes deploys Dask workers on Kubernetes clusters using native Kubernetes APIs.
    > It is designed to dynamically launch short-lived deployments of workers
    > during the lifetime of a Python process.

    The Dask job spawn a temporary adaptive Dask cluster with a
    Dask scheduler and workers to run your container.

    Args:
        kind: str, should be equal `dask`
        threads: int, optiona
        scale: int, optional
        adapt_min: int, optional
        adapt_max: int, optional
        adapt_interval: int, optional
        environment: [V1Environment](/docs/core/specification/environment/), optional
        connections: List[str], optional
        volumes: List[[Kubernetes Volume](https://kubernetes.io/docs/concepts/storage/volumes/)],
             optional
        init: List[[V1Init](/docs/core/specification/init/)], optional
        sidecars: List[[sidecar containers](/docs/core/specification/sidecars/)], optional
        container: [Kubernetes Container](https://kubernetes.io/docs/concepts/containers/)

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: dask
    >>>   threads:
    >>>   scale:
    >>>   adaptMin:
    >>>   adaptMax:
    >>>   adaptInterval:
    >>>   environment:
    >>>   connections:
    >>>   volumes:
    >>>   init:
    >>>   sidecars:
    >>>   container:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.polyflow import V1Environment, V1Init, V1Dask
    >>> from polyaxon.k8s import k8s_schemas
    >>> dask_job = V1Dask(
    >>>     threads=2,
    >>>     scale=None,
    >>>     adapt_min=1,
    >>>     adapt_max=100,
    >>>     adapt_interval=1000,
    >>>     environment=V1Environment(...),
    >>>     connections=["connection-name1"],
    >>>     volumes=[k8s_schemas.V1Volume(...)],
    >>>     init=[V1Init(...)],
    >>>     sidecars=[k8s_schemas.V1Container(...)],
    >>>     container=k8s_schemas.V1Container(...),
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that
    this component's runtime is a dask job.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: dask
    ```

    ### threads

    Number of threads to pass to the Dask worker, default is `1`.

    ```yaml
    >>> run:
    >>>   kind: dask
    >>>   threads: 2
    ```

    ### scale

    To specify number of workers explicitly.

    ```yaml
    >>> run:
    >>>   kind: dask
    >>>   scale: 20
    ```


    ### adaptMin

    To specify adaptive mode min workers and dynamically scale based on current workload.

    ```yaml
    >>> run:
    >>>   kind: dask
    >>>   adaptMin: 2
    ```

    ### adaptMax

    To specify adaptive mode max workers and dynamically scale based on current workload.

    ```yaml
    >>> run:
    >>>   kind: dask
    >>>   adaptMax: 20
    ```

    ### adaptInterval

    To specify adaptive mode interval check, default `1000 ms`.

    ```yaml
    >>> run:
    >>>   kind: dask
    >>>   adaptInterval: 20000
    ```

    ### environment

    Optional [environment section](/docs/core/specification/environment/),
    it provides a way to inject pod related information.

    ```yaml
    >>> run:
    >>>   kind: dask
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

    ### connections

    A list of [connection names](/docs/setup/connections/) to resolve for the job.

    <blockquote class="light">
    If you are referencing a connection it must be configured.
    All referenced connections will be checked:

     * If they are accessible in the context of the project of this run

     * If the user running the operation can have access to those connections
    </blockquote>

    After checks, the connections will be resolved and inject any volumes, secrets, configMaps,
    environment variables for your main container to function correctly.

    ```yaml
    >>> run:
    >>>   kind: dask
    >>>   connections: [connection1, connection2]
    ```

    ### volumes

    A list of [Kubernetes Volumes](https://kubernetes.io/docs/concepts/storage/volumes/)
    to resolve and mount for your jobs.

    This is an advanced use-case where configuring a connection is not an option.

    When you add a volume you need to mount it manually to your container(s).

    ```yaml
    >>> run:
    >>>   kind: dask
    >>>   volumes:
    >>>     - name: volume1
    >>>       persistentVolumeClaim:
    >>>         claimName: pvc1
    >>>   ...
    >>>   container:
    >>>     name: myapp-container
    >>>     image: busybox:1.28
    >>>     command: ['sh', '-c', 'echo custom init container']
    >>>     volumeMounts:
    >>>     - name: volume1
    >>>       mountPath: /mnt/vol/path
    ```

    ### init

    A list of [init handlers and containers](/docs/core/specification/init/)
    to resolve for the job.

    <blockquote class="light">
    If you are referencing a connection it must be configured.
    All referenced connections will be checked:

     * If they are accessible in the context of the project of this run

     * If the user running the operation can have access to those connections
    </blockquote>

    ```yaml
    >>> run:
    >>>   kind: dask
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
    >>> run:
    >>>   kind: dask
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
    that will run your experiment training or data processing logic.

    ```yaml
    >>> run:
    >>>   kind: dask
    >>>   container:
    >>>     name: tensorflow:2.1
    >>>     init:
    >>>       - connection: my-tf-code-repo
    >>>     command: ["python", "/plx-context/artifacts/my-tf-code-repo/model.py"]
    ```
    """

    _IDENTIFIER = V1RunKind.DASK
    _SWAGGER_FIELDS = ["volumes", "sidecars", "container"]

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    threads: Optional[IntOrRef]
    scale: Optional[IntOrRef]
    adapt_min: Optional[IntOrRef] = Field(alias="adaptMin")
    adapt_max: Optional[IntOrRef] = Field(alias="adaptMax")
    adapt_interval: Optional[IntOrRef] = Field(alias="adaptInterval")
    environment: Optional[Union[V1Environment, RefField]]
    connections: Optional[Union[List[StrictStr], RefField]]
    volumes: Optional[Union[List[k8s_schemas.V1Volume], RefField]]
    init: Optional[Union[List[V1Init], RefField]]
    sidecars: Optional[Union[List[k8s_schemas.V1Container], RefField]]
    container: Optional[Union[k8s_schemas.V1Container, RefField]]

    @validator("volumes", always=True, pre=True)
    def validate_volumes(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_volume(vi) for vi in v]

    @validator("sidecars", always=True, pre=True)
    def validate_helper_containers(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_container(vi) for vi in v]

    @validator("container", always=True, pre=True)
    def validate_container(cls, v):
        return k8s_validation.validate_k8s_container(v)
