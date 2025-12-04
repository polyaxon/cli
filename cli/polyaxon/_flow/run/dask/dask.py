from typing import Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field
from clipped.types.ref_or_obj import IntOrRef, RefField

from polyaxon._flow.run.base import BaseRun
from polyaxon._flow.run.dask.replica import V1DaskReplica
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.resources import V1RunResources
from polyaxon._flow.run.utils import DestinationImageMixin
from polyaxon._k8s.k8s_schemas import V1Container


class V1DaskCluster(BaseRun, DestinationImageMixin):
    """Dask cluster specification for running distributed workloads.
    [Dask cluster](https://kubernetes.dask.org/en/latest/).

    Creates a Dask cluster with scheduler and worker replicas.
    Platform automatically handles service, health checks, and dashboard configuration.

    Args:
        kind: str, should be equal `daskcluster`
        worker: V1DaskReplica, optional - Worker replica specification
        scheduler: V1DaskReplica, optional - Scheduler replica specification
        min_replicas: int, optional - Minimum number of workers for autoscaling
        max_replicas: int, optional - Maximum number of workers for autoscaling

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: daskcluster
    >>>   worker:
    >>>     replicas: 3
    >>>     container:
    >>>       image: daskdev/dask:latest
    >>>       resources:
    >>>         requests:
    >>>           memory: 2Gi
    >>>           cpu: 1
    >>>   scheduler:
    >>>     container:
    >>>       image: daskdev/dask:latest
    >>>       resources:
    >>>         requests:
    >>>           memory: 1Gi
    >>>           cpu: 1
    ```

    ## Autoscaling

    Enable autoscaling by setting `minReplicas` and `maxReplicas`.
    When both are set, a DaskAutoscaler resource will be created.

    ```yaml
    >>> run:
    >>>   kind: daskcluster
    >>>   minReplicas: 1
    >>>   maxReplicas: 10
    >>>   worker:
    >>>     replicas: 2
    >>>     container:
    >>>       image: daskdev/dask:latest
    >>>   scheduler:
    >>>     container:
    >>>       image: daskdev/dask:latest
    ```
    """

    _IDENTIFIER = V1RunKind.DASKCLUSTER
    _CUSTOM_DUMP_FIELDS = {"worker", "scheduler"}

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    worker: Optional[Union[V1DaskReplica, RefField]] = None
    scheduler: Optional[Union[V1DaskReplica, RefField]] = None
    min_replicas: Optional[IntOrRef] = Field(alias="minReplicas", default=None)
    max_replicas: Optional[IntOrRef] = Field(alias="maxReplicas", default=None)

    def apply_image_destination(self, image: str):
        if self.worker:
            self.worker.container = self.worker.container or V1Container()
            self.worker.container.image = image
        if self.scheduler:
            self.scheduler.container = self.scheduler.container or V1Container()
            self.scheduler.container.image = image

    def get_resources(self):
        resources = V1RunResources()
        if self.worker:
            resources += self.worker.get_resources()
        if self.scheduler:
            resources += self.scheduler.get_resources()
        return resources

    def get_all_containers(self):
        containers = []
        if self.worker:
            containers += self.worker.get_all_containers()
        if self.scheduler:
            containers += self.scheduler.get_all_containers()
        return containers

    def get_all_connections(self):
        connections = []
        if self.worker:
            connections += self.worker.get_all_connections()
        if self.scheduler:
            connections += self.scheduler.get_all_connections()
        return connections

    def get_all_init(self):
        init = []
        if self.worker:
            init += self.worker.get_all_init()
        if self.scheduler:
            init += self.scheduler.get_all_init()
        return init

    def get_replica_types(self):
        types = []
        if self.worker:
            types.append("worker")
        if self.scheduler:
            types.append("scheduler")
        return types
