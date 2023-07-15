from typing import Optional, Union
from typing_extensions import Literal

from clipped.types.ref_or_obj import RefField

from polyaxon.polyflow.run.base import BaseRun
from polyaxon.polyflow.run.dask.replica import V1DaskReplica
from polyaxon.polyflow.run.kinds import V1RunKind


class V1DaskJob(BaseRun):
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
    >>> from polyaxon.polyflow import V1Environment, V1Init, V1DaskJob, V1DaskReplica
    >>> from polyaxon.k8s import k8s_schemas
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
