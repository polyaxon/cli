from typing import Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field
from clipped.types.ref_or_obj import RefField

from polyaxon._flow.run.base import BaseRun
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.kubeflow.clean_pod_policy import V1CleanPodPolicy
from polyaxon._flow.run.kubeflow.replica import V1KFReplica
from polyaxon._flow.run.kubeflow.scheduling_policy import V1SchedulingPolicy
from polyaxon._flow.run.resources import V1RunResources
from polyaxon._flow.run.utils import DestinationImageMixin
from polyaxon._k8s.k8s_schemas import V1Container


class V1XGBoostJob(BaseRun, DestinationImageMixin):
    """Kubeflow XGBoost-Job provides an interface to train distributed experiments with XGBoost.

    Args:
        kind: str, should be equal `xgbjob`
        clean_pod_policy: str, one of [`All`, `Running`, `None`]
        scheduling_policy: [V1SchedulingPolicy](/docs/experimentation/distributed/kubeflow-scheduling-policy/), optional  # noqa
        master: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional
        worker: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: xgbjob
    >>>   cleanPodPolicy:
    >>>   schedulingPolicy:
    >>>   master:
    >>>   worker:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1KFReplica, V1XGBoostJob
    >>> xgb_job = V1XGBoostJob(
    >>>     clean_pod_policy='All',
    >>>     master=V1KFReplica(...),
    >>>     worker=V1KFReplica(...),
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this component's runtime is a xgbjob.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: xgbjob
    ```

    ### cleanPodPolicy

    Controls the deletion of pods when a job terminates.
    The policy can be one of the following values: [`All`, `Running`, `None`]


    ```yaml
    >>> run:
    >>>   kind: xgbjob
    >>>   cleanPodPolicy: 'All'
    >>>  ...
    ```

    ### schedulingPolicy

    SchedulingPolicy encapsulates various scheduling policies of the distributed training
    job, for example `minAvailable` for gang-scheduling.


    ```yaml
    >>> run:
    >>>   kind: xgbjob
    >>>   schedulingPolicy:
    >>>     ...
    >>>  ...
    ```

    ### master

    The master replica in the distributed XGBoostJob.

    ```yaml
    >>> run:
    >>>   kind: xgbjob
    >>>   ps:
    >>>     replicas: 2
    >>>     container:
    >>>       ...
    >>>  ...
    ```

    ### worker

    The server replica in the distributed XGBoostJob.

    ```yaml
    >>> run:
    >>>   kind: xgbjob
    >>>   worker:
    >>>     replicas: 2
    >>>     container:
    >>>       ...
    >>>  ...
    ```
    """

    _IDENTIFIER = V1RunKind.XGBJOB

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    clean_pod_policy: Optional[V1CleanPodPolicy] = Field(alias="cleanPodPolicy")
    scheduling_policy: Optional[V1SchedulingPolicy] = Field(alias="schedulingPolicy")
    master: Optional[Union[V1KFReplica, RefField]]
    worker: Optional[Union[V1KFReplica, RefField]]

    def apply_image_destination(self, image: str):
        if self.chief:
            self.chief.container = self.chief.container or V1Container()
            self.chief.container.image = image
        if self.ps:
            self.ps.container = self.ps.container or V1Container()
            self.ps.container.image = image
        if self.worker:
            self.worker.container = self.worker.container or V1Container()
            self.worker.container.image = image
        if self.evaluator:
            self.evaluator.container = self.evaluator.container or V1Container()
            self.evaluator.container.image = image

    def get_resources(self):
        resources = V1RunResources()
        if self.chief:
            resources += self.chief.get_resources()
        if self.ps:
            resources += self.ps.get_resources()
        if self.worker:
            resources += self.worker.get_resources()
        if self.evaluator:
            resources += self.evaluator.get_resources()
        return resources

    def get_all_containers(self):
        containers = []
        if self.chief:
            containers += self.chief.get_all_containers()
        if self.ps:
            containers += self.ps.get_all_containers()
        if self.worker:
            containers += self.worker.get_all_containers()
        if self.evaluator:
            containers += self.evaluator.get_all_containers()
        return containers

    def get_all_connections(self):
        connections = []
        if self.chief:
            connections += self.chief.get_all_connections()
        if self.ps:
            connections += self.ps.get_all_connections()
        if self.worker:
            connections += self.worker.get_all_connections()
        if self.evaluator:
            connections += self.evaluator.get_all_connections()
        return connections

    def get_all_init(self):
        init = []
        if self.chief:
            init += self.chief.get_all_init()
        if self.ps:
            init += self.ps.get_all_init()
        if self.worker:
            init += self.worker.get_all_init()
        if self.evaluator:
            init += self.evaluator.get_all_init()
        return init
