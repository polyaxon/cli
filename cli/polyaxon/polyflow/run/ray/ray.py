from typing import Any, Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.types.ref_or_obj import RefField
from pydantic import Field

from polyaxon.k8s.k8s_schemas import V1Container
from polyaxon.polyflow.run.base import BaseRun
from polyaxon.polyflow.run.kinds import V1RunKind
from polyaxon.polyflow.run.ray.replica import V1RayReplica
from polyaxon.polyflow.run.resources import V1RunResources
from polyaxon.polyflow.run.utils import DestinationImageMixin


class V1RayJob(BaseRun, DestinationImageMixin):
    """Ray jobs are used to run Ray applications on Kubernetes.

    [Ray](https://www.ray.io/) Ray is an open-source unified compute framework that makes
    it easy to scale AI and Python workloads,
    from reinforcement learning to deep learning to tuning, and model serving.

    Args:
        kind: str, should be equal `rayjob`
        entrypoint: str, optional
        runtime_env: Dict, optional
        metadata: int, Dict, optional
        ray_version: str, optional
        head: [V1RayReplica](/docs/experimentation/distributed/ray-replica/), optional
        workers: Dict[str, [V1RayReplica](/docs/experimentation/distributed/ray-replica/)], optional


    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: rayjob
    >>>   entrypoint:
    >>>   runtimeRnv:
    >>>   metadata:
    >>>   rayVersion:
    >>>   head:
    >>>   workers:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.polyflow import V1Environment, V1Init, V1RayJob, V1RayReplica
    >>> from polyaxon.k8s import k8s_schemas
    >>> ray_job = V1Ray(
    >>>     connections=["connection-name1"],
    >>>     volumes=[k8s_schemas.V1Volume(...)],
    >>>     ray_version="2.5.0",
    >>>     head=V1RayReplica(...),
    >>>     worker=V1RayReplica(...),
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this component's runtime is a job.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: rayjob
    ```

    ### entrypoint

    The entrypoint command for this job.

    ```yaml
    >>> run:
    >>>   kind: rayjob
    >>>   entrypoint: python train.py
    ```

    ### runtimeEnv

    The runtime environment for this job.

    ```yaml
    >>> run:
    >>>   kind: rayjob
    >>>   runtimeEnv:
    >>>     pip: ["requests==2.26.0", "pendulum==2.1.2"]
    >>>     env_vars: {"counter_name": "test_counter"}
    ```

    ### rayVersion

    The version of Ray the application uses.

    ```yaml
    >>> run:
    >>>   kind: rayjob
    >>>   rayVersion: 2.5.0
    >>>   ...
    ```

    ### head

    Ray head replica specification

    ```yaml
    >>> run:
    >>>   kind: rayjob
    >>>   head:
    >>>     rayStartParams:
    >>>       dashboard-host: '0.0.0.0'
    >>>     container:
    >>>     ...
    >>>   ...
    ```

    ### workers

    List of worker replica specifications

    ```yaml
    >>> run:
    >>>   kind: rayjob
    >>>   workers:
    >>>     small-group:
    >>>       replicas: 1
    >>>       minReplicas: 1
    >>>       maxReplicas: 5
    >>>     ...
    >>>   ...
    ```
    """

    _IDENTIFIER = V1RunKind.RAYJOB

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    entrypoint: Optional[str]
    runtime_env: Optional[Union[Dict[str, Any], RefField]] = Field(alias="runtimeEnv")
    metadata: Optional[Union[Dict[str, str], RefField]]
    ray_version: Optional[str] = Field(alias="rayVersion")
    head: Optional[Union[V1RayReplica, RefField]]
    workers: Optional[Dict[str, Union[V1RayReplica, RefField]]]

    def apply_image_destination(self, image: str):
        if self.head:
            self.head.container = self.head.container or V1Container()
            self.head.container.image = image
        if self.workers:
            for worker_name in self.workers:
                worker = self.workers[worker_name]
                worker.container = worker.container or V1Container()
                worker.container.image = image

    def get_resources(self):
        resources = V1RunResources()
        if self.head:
            resources += self.head.get_resources()
        if self.workers:
            for worker_name in self.workers:
                worker = self.workers[worker_name]
                resources += worker.get_resources()
        return resources

    def get_all_containers(self):
        containers = []
        if self.head:
            containers += self.head.get_all_containers()
        if self.workers:
            for worker_name in self.workers:
                worker = self.workers[worker_name]
                containers += worker.get_all_containers()
        return containers

    def get_all_connections(self):
        connections = []
        if self.head:
            connections += self.head.get_all_connections()
        if self.workers:
            for worker_name in self.workers:
                worker = self.workers[worker_name]
                connections += worker.get_all_connections()
        return connections

    def get_all_init(self):
        init = []
        if self.head:
            init += self.head.get_all_init()
        if self.workers:
            for worker_name in self.workers:
                worker = self.workers[worker_name]
                init += worker.get_all_init()
        return init
