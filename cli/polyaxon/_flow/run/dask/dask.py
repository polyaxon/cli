from typing import Optional, Union
from typing_extensions import Literal

from clipped.types.ref_or_obj import RefField

from polyaxon._flow.run.base import BaseRun
from polyaxon._flow.run.dask.replica import V1DaskReplica
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.resources import V1RunResources
from polyaxon._flow.run.utils import DestinationImageMixin
from polyaxon._k8s.k8s_schemas import V1Container


class V1DaskJob(BaseRun, DestinationImageMixin):
    """Dask jobs are used to run distributed jobs using a
    [Dask cluster](https://kubernetes.dask.org/en/latest/).

    > Dask Kubernetes deploys Dask workers on Kubernetes clusters using native Kubernetes APIs.
    > It is designed to dynamically launch short-lived deployments of workers
    > during the lifetime of a job.

    The Dask job spawn a temporary adaptive Dask cluster with a
    Dask scheduler and workers to run your container.

    Args:
        kind: str, should be equal `daskjob`
        job: [V1DaskReplica](/docs/experimentation/distributed/dask-replica/), optional
        worker: [V1DaskReplica](/docs/experimentation/distributed/dask-replica/), optional
        scheduler: [V1DaskReplica](/docs/experimentation/distributed/dask-replica/), optional


    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: daskjob
    >>>   job:
    >>>   worker:
    >>>   scheduler:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Environment, V1Init, V1DaskJob, V1DaskReplica
    >>> dask_job = V1DaskJob(
    >>>     job=V1DaskReplica(...),
    >>>     worker=V1DaskReplica(...),
    >>>     scheduler=V1DaskReplica(...),
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this component's runtime is a job.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: daskjob
    ```

    ### job

    Dask head replica specification

    ```yaml
    >>> run:
    >>>   kind: daskjob
    >>>   job:
    >>>     container:
    >>>       image: "ghcr.io/dask/dask:latest"
    >>>       args:
    >>>       - python
    >>>       - -c
    >>>       - "from dask.distributed import Client; client = Client(); # Do some work..."
    >>>     ...
    >>>   ...
    ```

    ### worker

    List of worker replica specifications

    ```yaml
    >>> run:
    >>>   kind: daskjob
    >>>   worker:
    >>>     replicas: 2
    >>>     container:
    >>>       image: "ghcr.io/dask/dask:latest"
    >>>       args:
    >>>       - dask-worker
    >>>       - --nthreads
    >>>       - "2"
    >>>       - --name
    >>>       - $(DASK_WORKER_NAME)
    >>>       - --dashboard
    >>>       - --dashboard-address
    >>>       - "8788"
    >>>   ...
    ```

    ### scheduler

    Dask scheduler replica specification

    ```yaml
    >>> run:
    >>>   kind: daskjob
    >>>   scheduler:
    >>>     container:
    >>>       image: "ghcr.io/dask/dask:latest"
    >>>       args:
    >>>       - dask-scheduler
    >>>       - --dashboard-address
    >>>       - "8787"
    >>>   ...
    ```
    """

    _IDENTIFIER = V1RunKind.DASKJOB
    _SWAGGER_FIELDS = ["volumes", "sidecars", "container"]

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    job: Optional[Union[V1DaskReplica, RefField]]
    worker: Optional[Union[V1DaskReplica, RefField]]
    scheduler: Optional[Union[V1DaskReplica, RefField]]

    def apply_image_destination(self, image: str):
        if self.job:
            self.job.container = self.job.container or V1Container()
            self.job.container.image = image

    def get_resources(self):
        resources = V1RunResources()
        if self.job:
            resources += self.job.get_resources()
        if self.worker:
            resources += self.worker.get_resources()
        if self.scheduler:
            resources += self.scheduler.get_resources()
        return resources

    def get_all_containers(self):
        containers = []
        if self.job:
            containers += self.job.get_all_containers()
        if self.worker:
            containers += self.worker.get_all_containers()
        if self.scheduler:
            containers += self.scheduler.get_all_containers()
        return containers

    def get_all_connections(self):
        connections = []
        if self.job:
            connections += self.job.get_all_connections()
        if self.worker:
            connections += self.worker.get_all_connections()
        if self.scheduler:
            connections += self.scheduler.get_all_connections()
        return connections

    def get_all_init(self):
        init = []
        if self.job:
            init += self.job.get_all_init()
        if self.worker:
            init += self.worker.get_all_init()
        if self.scheduler:
            init += self.scheduler.get_all_init()
        return init
