from typing import Dict, List, Optional, Union
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
from polyaxon._schemas.base import BaseSchemaModel


class V1PaddleElasticPolicy(BaseSchemaModel):
    """Elastic policy for Paddle distributed runs.

    Args:
        minReplicas: int, optional
        maxReplicas: int, optional
        maxRestarts: int, optional
        metrics: List[Dict], optional
    """

    _IDENTIFIER = "elasticPolicy"

    min_replicas: Optional[IntOrRef] = Field(alias="minReplicas")
    max_replicas: Optional[IntOrRef] = Field(alias="maxReplicas")
    max_restarts: Optional[IntOrRef] = Field(alias="maxRestarts")
    metrics: Optional[List[Dict]] = Field(alias="Metrics")


class V1PaddleJob(BaseRun, DestinationImageMixin):
    """Kubeflow PaddlePaddle-Job provides an interface to train distributed
    experiments with PaddlePaddle.

    Args:
        kind: str, should be equal `paddlejob`
        clean_pod_policy: str, one of [`All`, `Running`, `None`]
        scheduling_policy: [V1SchedulingPolicy](/docs/experimentation/distributed/kubeflow-scheduling-policy/), optional  # noqa
        master: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional
        worker: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: paddlejob
    >>>   cleanPodPolicy:
    >>>   schedulingPolicy:
    >>>   master:
    >>>   worker:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1KFReplica, V1PaddleJob
    >>> paddle_job = V1PaddleJob(
    >>>     clean_pod_policy='All',
    >>>     masterf=V1KFReplica(...),
    >>>     worker=V1KFReplica(...),
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this component's runtime is a paddlejob.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: paddlejob
    ```

    ### cleanPodPolicy

    Controls the deletion of pods when a job terminates.
    The policy can be one of the following values: [`All`, `Running`, `None`]


    ```yaml
    >>> run:
    >>>   kind: paddlejob
    >>>   cleanPodPolicy: 'All'
    >>>  ...
    ```

    ### schedulingPolicy

    SchedulingPolicy encapsulates various scheduling policies of the distributed training
    job, for example `minAvailable` for gang-scheduling.


    ```yaml
    >>> run:
    >>>   kind: paddlejob
    >>>   schedulingPolicy:
    >>>     ...
    >>>  ...
    ```

    ### elasticPolicy

    Elastic policy for Paddle distributed runs.

    ```yaml
    >>> run:
    >>>   kind: paddlejob
    >>>   elasticPolicy:
    >>>     ...
    >>>  ...
    ```

    ### master

    The ,aster is responsible for orchestrating training and performing
    tasks like checkpointing the model.

    ```yaml
    >>> run:
    >>>   kind: paddlejob
    >>>   master:
    >>>     replicas: 1
    >>>     container:
    >>>       ...
    >>>  ...
    ```

    ### worker

    The workers do the actual work of training the model. In some cases,
    worker 0 might also act as the chief.

    ```yaml
    >>> run:
    >>>   kind: paddlejob
    >>>   worker:
    >>>     replicas: 2
    >>>     container:
    >>>       ...
    >>>  ...
    ```
    """

    _IDENTIFIER = V1RunKind.PADDLEJOB

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    clean_pod_policy: Optional[V1CleanPodPolicy] = Field(alias="cleanPodPolicy")
    scheduling_policy: Optional[V1SchedulingPolicy] = Field(alias="schedulingPolicy")
    elastic_policy: Optional[V1PaddleElasticPolicy] = Field(alias="elasticPolicy")
    master: Optional[Union[V1KFReplica, RefField]]
    worker: Optional[Union[V1KFReplica, RefField]]

    def apply_image_destination(self, image: str):
        if self.master:
            self.master.container = self.master.container or V1Container()
            self.master.container.image = image
        if self.worker:
            self.worker.container = self.worker.container or V1Container()
            self.worker.container.image = image

    def get_resources(self):
        resources = V1RunResources()
        if self.master:
            resources += self.master.get_resources()
        if self.worker:
            resources += self.worker.get_resources()
        return resources

    def get_all_containers(self):
        containers = []
        if self.master:
            containers += self.master.get_all_containers()
        if self.worker:
            containers += self.worker.get_all_containers()
        return containers

    def get_all_connections(self):
        connections = []
        if self.master:
            connections += self.master.get_all_connections()
        if self.worker:
            connections += self.worker.get_all_connections()
        return connections

    def get_all_init(self):
        init = []
        if self.master:
            init += self.master.get_all_init()
        if self.worker:
            init += self.worker.get_all_init()
        return init
