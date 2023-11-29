from typing import Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field
from clipped.types.ref_or_obj import RefField
from clipped.utils.enums import PEnum

from polyaxon._flow.run.base import BaseRun
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.kubeflow.clean_pod_policy import V1CleanPodPolicy
from polyaxon._flow.run.kubeflow.replica import V1KFReplica
from polyaxon._flow.run.kubeflow.scheduling_policy import V1SchedulingPolicy
from polyaxon._flow.run.resources import V1RunResources
from polyaxon._flow.run.utils import DestinationImageMixin
from polyaxon._k8s.k8s_schemas import V1Container


class MXJobMode(str, PEnum):
    MX_TRAIN = "MXTrain"
    MX_TUNE = "MXTune"


class V1MXJob(BaseRun, DestinationImageMixin):
    """Kubeflow MXNet-Job provides an interface to train distributed experiments with MXNet.

    Args:
        kind: str, should be equal `mxjob`
        clean_pod_policy: str, one of [`All`, `Running`, `None`]
        scheduling_policy: [V1SchedulingPolicy](/docs/experimentation/distributed/kubeflow-scheduling-policy/), optional  # noqa
        mode: str, one of [`MXTrain`, `MXTune`]
        scheduler: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional
        server: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional
        worker: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional
        tuner: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional
        tuner_tracker: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional
        tuner_server: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: mxjob
    >>>   cleanPodPolicy:
    >>>   schedulingPolicy:
    >>>   mode:
    >>>   scheduler:
    >>>   server:
    >>>   worker:
    >>>   tuner:
    >>>   tunerTracker:
    >>>   tunerServer:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1KFReplica, V1MXJob
    >>> mx_job = V1MXJob(
    >>>     clean_pod_policy='All',
    >>>     scheduler=V1KFReplica(...),
    >>>     server=V1KFReplica(...),
    >>>     worker=V1KFReplica(...),
    >>>     tuner=V1KFReplica(...),
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this component's runtime is a mxjob.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: mxjob
    ```

    ### cleanPodPolicy

    Controls the deletion of pods when a job terminates.
    The policy can be one of the following values: [`All`, `Running`, `None`]


    ```yaml
    >>> run:
    >>>   kind: mxjob
    >>>   cleanPodPolicy: 'All'
    >>>  ...
    ```

    ### schedulingPolicy

    SchedulingPolicy encapsulates various scheduling policies of the distributed training
    job, for example `minAvailable` for gang-scheduling.


    ```yaml
    >>> run:
    >>>   kind: mxjob
    >>>   schedulingPolicy:
    >>>     ...
    >>>  ...
    ```

    ### mode

    The kind of MXJob to schedule. Different mode may have different replicas.

    ```yaml
    >>> run:
    >>>   kind: mxjob
    >>>   mode: 'MXTrain'
    >>>  ...
    ```

    ### Scheduler

    Ths scheduler replica in the distributed MXJob.

    ```yaml
    >>> run:
    >>>   kind: mxjob
    >>>   scheduler:
    >>>     replicas: 2
    >>>     container:
    >>>       ...
    >>>  ...
    ```

    ### server

    The server replica in the distributed MXJob.

    ```yaml
    >>> run:
    >>>   kind: mxjob
    >>>   server:
    >>>     replicas: 2
    >>>     container:
    >>>       ...
    >>>  ...
    ```

    ### worker

    The worker replica in the distributed MXJob.

    ```yaml
    >>> run:
    >>>   kind: mxjob
    >>>   worker:
    >>>     replicas: 2
    >>>     container:
    >>>       ...
    >>>  ...
    ```

    ### tuner

    The tuner replica in the distributed MXJob.

    ```yaml
    >>> run:
    >>>   kind: mxjob
    >>>   tuner:
    >>>     replicas: 1
    >>>     container:
    >>>       ...
    >>>  ...
    ```

    ### tunerTracker

    The tuner tracker replica in the distributed MXJob.

    ```yaml
    >>> run:
    >>>   kind: mxjob
    >>>   tunerTracker:
    >>>     replicas: 1
    >>>     container:
    >>>       ...
    >>>  ...
    ```

    ### tunerServer

    The tuner server replica in the distributed MXJob.

    ```yaml
    >>> run:
    >>>   kind: mxjob
    >>>   tunerServer:
    >>>     replicas: 1
    >>>     container:
    >>>       ...
    >>>  ...
    ```
    """

    _IDENTIFIER = V1RunKind.MXJOB

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    clean_pod_policy: Optional[V1CleanPodPolicy] = Field(alias="cleanPodPolicy")
    scheduling_policy: Optional[V1SchedulingPolicy] = Field(alias="schedulingPolicy")
    mode: Optional[MXJobMode]
    scheduler: Optional[Union[V1KFReplica, RefField]]
    server: Optional[Union[V1KFReplica, RefField]]
    worker: Optional[Union[V1KFReplica, RefField]]
    tuner: Optional[Union[V1KFReplica, RefField]]
    tuner_tracker: Optional[Union[V1KFReplica, RefField]] = Field(alias="tunerTracker")
    tuner_server: Optional[Union[V1KFReplica, RefField]] = Field(alias="tunerServer")

    def apply_image_destination(self, image: str):
        if self.scheduler:
            self.scheduler.container = self.scheduler.container or V1Container()
            self.scheduler.container.image = image
        if self.server:
            self.server.container = self.server.container or V1Container()
            self.server.container.image = image
        if self.worker:
            self.worker.container = self.worker.container or V1Container()
            self.worker.container.image = image
        if self.tuner:
            self.tuner.container = self.tuner.container or V1Container()
            self.tuner.container.image = image
        if self.tuner_tracker:
            self.tuner_tracker.container = self.tuner_tracker.container or V1Container()
            self.tuner_tracker.container.image = image
        if self.tuner_server:
            self.tuner_server.container = self.tuner_server.container or V1Container()
            self.tuner_server.container.image = image

    def get_resources(self):
        resources = V1RunResources()
        if self.scheduler:
            resources += self.scheduler.get_resources()
        if self.server:
            resources += self.server.get_resources()
        if self.worker:
            resources += self.worker.get_resources()
        if self.tuner:
            resources += self.tuner.get_resources()
        if self.tuner_tracker:
            resources += self.tuner_tracker.get_resources()
        if self.tuner_server:
            resources += self.tuner_server.get_resources()
        return resources

    def get_all_containers(self):
        containers = []
        if self.scheduler:
            containers += self.scheduler.get_all_containers()
        if self.server:
            containers += self.server.get_all_containers()
        if self.worker:
            containers += self.worker.get_all_containers()
        if self.tuner:
            containers += self.tuner.get_all_containers()
        if self.tuner_tracker:
            containers += self.tuner_tracker.get_all_containers()
        if self.tuner_server:
            containers += self.tuner_server.get_all_containers()
        return containers

    def get_all_connections(self):
        connections = []
        if self.scheduler:
            connections += self.scheduler.get_all_connections()
        if self.server:
            connections += self.server.get_all_connections()
        if self.worker:
            connections += self.worker.get_all_connections()
        if self.tuner:
            connections += self.tuner.get_all_connections()
        if self.tuner_tracker:
            connections += self.tuner_tracker.get_all_connections()
        if self.tuner_server:
            connections += self.tuner_server.get_all_connections()
        return connections

    def get_all_init(self):
        init = []
        if self.scheduler:
            init += self.scheduler.get_all_init()
        if self.server:
            init += self.server.get_all_init()
        if self.worker:
            init += self.worker.get_all_init()
        if self.tuner:
            init += self.tuner.get_all_init()
        if self.tuner_tracker:
            init += self.tuner_tracker.get_all_init()
        if self.tuner_server:
            init += self.tuner_server.get_all_init()
        return init
