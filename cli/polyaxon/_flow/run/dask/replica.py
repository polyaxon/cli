from typing import List, Optional, Union

from clipped.compact.pydantic import StrictStr, validator
from clipped.types.ref_or_obj import IntOrRef, RefField

from polyaxon._flow.environment import V1Environment
from polyaxon._flow.init import V1Init
from polyaxon._flow.run.resources import V1RunResources
from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon._schemas.base import BaseSchemaModel


class V1DaskReplica(BaseSchemaModel):
    """Dask replica is the specification for a Dask job, worker or scheduler.

    Args:
        replicas: str, optional int
        environment: [V1Environment](/docs/core/specification/environment/), optional
        connections: List[str], optional
        volumes: List[[Kubernetes Volume](https://kubernetes.io/docs/concepts/storage/volumes/)],
             optional
        init: List[[V1Init](/docs/core/specification/init/)], optional
        sidecars: List[[sidecar containers](/docs/core/specification/sidecars/)], optional
        container: [Kubernetes Container](https://kubernetes.io/docs/concepts/containers/)

    ## YAML usage

    ```yaml
    >>> head/worker:
    >>>   replicas:
    >>>   environment:
    >>>   connections:
    >>>   volumes:
    >>>   init:
    >>>   sidecars:
    >>>   container:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Environment, V1Init, V1DaskReplica
    >>> from polyaxon import k8s
    >>> replica = V1DaskReplica(
    >>>     replicas=2,
    >>>     environment=V1Environment(...),
    >>>     init=[V1Init(...)],
    >>>     sidecars=[k8s.V1Container(...)],
    >>>     container=k8s.V1Container(...),
    >>> )
    ```

    ## Fields

    ### replicas

    The number of worker replica instances.

    ```yaml
    >>> executor:
    >>>   replicas: 2
    ```

    ### environment

    Optional [environment section](/docs/core/specification/environment/),
    it provides a way to inject pod related information into the replica (executor/driver).

    ```yaml
    >>> worker:
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
    >>> worker:
    >>>   connections: [connection1, connection2]
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
    >>> worker:
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
    that will be used as sidecars.

    ```yaml
    >>> worker:
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
    >>> worker:
    >>>   init:
    >>>     - connection: my-code-repo
    >>>   container:
    >>>     name: tensorflow:2.1
    >>>     command: ["python", "/plx-context/artifacts/my-code-repo/model.py"]
    ```
    """

    _IDENTIFIER = "replica"
    _SWAGGER_FIELDS = ["volumes", "sidecars", "container"]

    replicas: Optional[IntOrRef]
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

    def get_resources(self):
        resources = V1RunResources()
        for i in range(self.replicas or 1):
            resources += V1RunResources.from_container(self.container)

        return resources

    def get_all_containers(self):
        return [self.container] if self.container else []

    def get_all_connections(self):
        return self.connections or []

    def get_all_init(self):
        return self.init or []
