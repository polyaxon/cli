from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field, StrictStr
from clipped.types.ref_or_obj import BoolOrRef, IntOrRef, RefField

from polyaxon._flow.run.base import BaseRun
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.kubeflow.clean_pod_policy import V1CleanPodPolicy
from polyaxon._flow.run.kubeflow.replica import V1KFReplica
from polyaxon._flow.run.kubeflow.scheduling_policy import V1SchedulingPolicy
from polyaxon._flow.run.resources import V1RunResources
from polyaxon._flow.run.utils import DestinationImageMixin
from polyaxon._k8s.k8s_schemas import V1Container
from polyaxon._schemas.base import BaseSchemaModel


class V1PytorchElasticPolicy(BaseSchemaModel):
    """Elastic policy for Pytorch distributed runs.

    Args:
        min_replicas: int, optional
        max_replicas: int, optional
        rdvz_backend: str, optional
        rdvz_port: int, optional
        rdvz_host: str, optional
        rdvz_id: str, optional
        rdvz_conf: List[Dict], optional
        standalone: bool, optional
        n_proc_per_node: int, optional
        max_restarts: int, optional
        metrics: List[Dict], optional
    """

    _IDENTIFIER = "elasticPolicy"

    min_replicas: Optional[IntOrRef] = Field(alias="minReplicas")
    max_replicas: Optional[IntOrRef] = Field(alias="maxReplicas")
    rdvz_backend: Optional[StrictStr] = Field(alias="rdvzBackend")
    rdvz_port: Optional[IntOrRef] = Field(alias="rdvzPort")
    rdvz_host: Optional[StrictStr] = Field(alias="rdvzHost")
    rdvz_id: Optional[StrictStr] = Field(alias="rdvzId")
    rdvz_conf: Optional[List[Dict]] = Field(alias="rdvzConf")
    standalone: Optional[BoolOrRef]
    n_proc_per_node: Optional[IntOrRef] = Field(alias="nProcPerNode")
    max_restarts: Optional[IntOrRef] = Field(alias="maxRestarts")
    metrics: Optional[List[Dict]] = Field(alias="Metrics")


class V1PytorchJob(BaseRun, DestinationImageMixin):
    """Kubeflow Pytorch-Job provides an interface to train distributed experiments with Pytorch.

    Args:
        kind: str, should be equal `pytorchjob`
        clean_pod_policy: str, one of [`All`, `Running`, `None`]
        scheduling_policy: [V1SchedulingPolicy](/docs/experimentation/distributed/kubeflow-scheduling-policy/), optional  # noqa
        master: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional
        worker: [V1KFReplica](/docs/experimentation/distributed/kubeflow-replica/), optional

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: pytorchjob
    >>>   cleanPodPolicy:
    >>>   schedulingPolicy:
    >>>   master:
    >>>   worker:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1KFReplica, V1PytorchJob
    >>> pytorch_job = V1PytorchJob(
    >>>     clean_pod_policy='All',
    >>>     master=V1KFReplica(...),
    >>>     worker=V1KFReplica(...),
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this
    component's runtime is a pytorchjob.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: pytorchjob
    ```

    ### cleanPodPolicy

    Controls the deletion of pods when a job terminates.
    The policy can be one of the following values: [`All`, `Running`, `None`]


    ```yaml
    >>> run:
    >>>   kind: pytorchjob
    >>>   cleanPodPolicy: 'All'
    >>>  ...
    ```

    ### schedulingPolicy

    SchedulingPolicy encapsulates various scheduling policies of the distributed training
    job, for example `minAvailable` for gang-scheduling.


    ```yaml
    >>> run:
    >>>   kind: pytorchjob
    >>>   schedulingPolicy:
    >>>     ...
    >>>  ...
    ```

    ### elasticPolicy

    ElasticPolicy encapsulates various policies for elastic distributed training job.

    ```yaml
    >>> run:
    >>>   kind: pytorchjob
    >>>   elasticPolicy:
    >>>     ...
    >>>  ...
    ```

    ### master

    The master replica in the distributed PytorchJob

    ```yaml
    >>> run:
    >>>   kind: pytorchjob
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
    >>>   kind: pytorchjob
    >>>   worker:
    >>>     replicas: 3
    >>>     container:
    >>>       ...
    >>>  ...
    ```
    """

    _IDENTIFIER = V1RunKind.PYTORCHJOB

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    clean_pod_policy: Optional[V1CleanPodPolicy] = Field(alias="cleanPodPolicy")
    scheduling_policy: Optional[V1SchedulingPolicy] = Field(alias="schedulingPolicy")
    elastic_policy: Optional[V1PytorchElasticPolicy] = Field(alias="elasticPolicy")
    n_proc_per_node: Optional[IntOrRef] = Field(alias="nProcPerNode")
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
