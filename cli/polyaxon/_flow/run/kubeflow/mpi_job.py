from typing import Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field
from clipped.types.ref_or_obj import IntOrRef, RefField

from polyaxon._flow.run.base import BaseRun
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.kubeflow.clean_pod_policy import V1CleanPodPolicy
from polyaxon._flow.run.kubeflow.replica import V1KFReplica
from polyaxon._flow.run.kubeflow.scheduling_policy import V1SchedulingPolicy
from polyaxon._flow.run.resources import V1RunResources
from polyaxon._flow.run.utils import DestinationImageMixin
from polyaxon._k8s.k8s_schemas import V1Container


class V1MPIJob(BaseRun, DestinationImageMixin):
    """Kubeflow MPI-Job provides an interface to train distributed experiments with MPI.

    Args:
        kind: str, should be equal `mpijob`
        clean_pod_policy: str, one of [`All`, `Running`, `None`]
        scheduling_policy: [V1SchedulingPolicy](/docs/experimentation/distributed/kubeflow-scheduling-policy/), optional  # noqa
        slots_per_worker: int, optional
        launcher: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional
        worker: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: mpijob
    >>>   cleanPodPolicy:
    >>>   schedulingPolicy:
    >>>   slotsPerWorker:
    >>>   launcher:
    >>>   worker:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1KFReplica, V1MPIJob
    >>> mpi_job = V1MPIJob(
    >>>     clean_pod_policy='All',
    >>>     launcher=V1KFReplica(...),
    >>>     worker=V1KFReplica(...),
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this
    component's runtime is a mpijob.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: mpijob
    ```

    ### cleanPodPolicy

    Controls the deletion of pods when a job terminates.
    The policy can be one of the following values: [`All`, `Running`, `None`]


    ```yaml
    >>> run:
    >>>   kind: mpijob
    >>>   cleanPodPolicy: 'All'
    >>>  ...
    ```

    ### schedulingPolicy

    SchedulingPolicy encapsulates various scheduling policies of the distributed training
    job, for example `minAvailable` for gang-scheduling.


    ```yaml
    >>> run:
    >>>   kind: mpijob
    >>>   schedulingPolicy:
    >>>     ...
    >>>  ...
    ```

     ### slotsPerWorker

    Specifies the number of slots per worker used in hostfile.
    Defaults to `1`.


    ```yaml
    >>> run:
    >>>   kind: mpijob
    >>>   slotsPerWorker: 2
    >>>  ...
    ```

    ### launcher

    The launcher replica in the distributed mpijob, automatica

    ```yaml
    >>> run:
    >>>   kind: mpijob
    >>>   master:
    >>>     replicas: 1
    >>>     container:
    >>>       ...
    >>>  ...
    ```

    ### worker

    The workers do the actual work of training the model.

    ```yaml
    >>> run:
    >>>   kind: mpijob
    >>>   worker:
    >>>     replicas: 3
    >>>     container:
    >>>       ...
    >>>  ...
    ```
    """

    _IDENTIFIER = V1RunKind.MPIJOB

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    clean_pod_policy: Optional[V1CleanPodPolicy] = Field(alias="cleanPodPolicy")
    scheduling_policy: Optional[V1SchedulingPolicy] = Field(alias="schedulingPolicy")
    slots_per_worker: Optional[IntOrRef] = Field(alias="slotsPerWorker")
    launcher: Optional[Union[V1KFReplica, RefField]]
    worker: Optional[Union[V1KFReplica, RefField]]

    def apply_image_destination(self, image: str):
        if self.launcher:
            self.launcher.container = self.launcher.container or V1Container()
            self.launcher.container.image = image
        if self.worker:
            self.worker.container = self.worker.container or V1Container()
            self.worker.container.image = image

    def get_resources(self):
        resources = V1RunResources()
        if self.launcher:
            resources += self.launcher.get_resources()
        if self.worker:
            resources += self.worker.get_resources()
        return resources

    def get_all_containers(self):
        containers = []
        if self.launcher:
            containers += self.launcher.get_all_containers()
        if self.worker:
            containers += self.worker.get_all_containers()
        return containers

    def get_all_connections(self):
        connections = []
        if self.launcher:
            connections += self.launcher.get_all_connections()
        if self.worker:
            connections += self.worker.get_all_connections()
        return connections

    def get_all_init(self):
        init = []
        if self.launcher:
            init += self.launcher.get_all_init()
        if self.worker:
            init += self.worker.get_all_init()
        return init
