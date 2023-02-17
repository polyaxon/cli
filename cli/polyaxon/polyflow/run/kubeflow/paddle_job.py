#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from marshmallow import fields, validate

import polyaxon_sdk

from polyaxon.k8s.k8s_schemas import V1Container
from polyaxon.polyflow.run.base import BaseRun
from polyaxon.polyflow.run.kinds import V1RunKind
from polyaxon.polyflow.run.kubeflow.clean_pod_policy import V1CleanPodPolicy
from polyaxon.polyflow.run.kubeflow.replica import KFReplicaSchema
from polyaxon.polyflow.run.kubeflow.scheduling_policy import SchedulingPolicySchema
from polyaxon.polyflow.run.resources import V1RunResources
from polyaxon.polyflow.run.utils import DestinationImageMixin
from polyaxon.schemas.base import BaseCamelSchema, BaseConfig


class PaddleJobSchema(BaseCamelSchema):
    kind = fields.Str(allow_none=True, validate=validate.Equal(V1RunKind.PADDLEJOB))
    clean_pod_policy = fields.Str(
        allow_none=True, validate=validate.OneOf(V1CleanPodPolicy.allowable_values)
    )
    scheduling_policy = fields.Nested(SchedulingPolicySchema, allow_none=True)
    master = fields.Nested(KFReplicaSchema, allow_none=True)
    worker = fields.Nested(KFReplicaSchema, allow_none=True)

    @staticmethod
    def schema_config():
        return V1PaddleJob


class V1PaddleJob(BaseConfig, BaseRun, DestinationImageMixin, polyaxon_sdk.V1PaddleJob):
    """Kubeflow PaddlePaddle-Job provides an interface to train distributed
    experiments with PaddlePaddle.

    Args:
        kind: str, should be equal `paddlejob`
        clean_pod_policy: str, one of [`All`, `Running`, `None`]
        scheduling_policy: [V1SchedulingPolicy](/docs/experimentation/distributed/scheduling-policy/), optional  # noqa
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
    >>> from polyaxon.polyflow import V1KFReplica, V1PaddleJob
    >>> from polyaxon.k8s import k8s_schemas
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

    SCHEMA = PaddleJobSchema
    IDENTIFIER = V1RunKind.PADDLEJOB
    REDUCED_ATTRIBUTES = [
        "cleanPodPolicy",
        "schedulingPolicy",
        "master",
        "worker",
    ]

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
