from typing import Union
from typing_extensions import Annotated

from clipped.compact.pydantic import Field

from polyaxon._flow.run.cleaner import V1CleanerJob
from polyaxon._flow.run.dag import V1Dag
from polyaxon._flow.run.dask import V1DaskCluster, V1DaskReplica
from polyaxon._flow.run.enums import (
    V1CloningKind,
    V1PipelineKind,
    V1RunEdgeKind,
    V1RunKind,
    V1RunPending,
)
from polyaxon._flow.run.job import V1Job
from polyaxon._flow.run.kubeflow.clean_pod_policy import V1CleanPodPolicy
from polyaxon._flow.run.kubeflow.mpi_job import V1MPIJob
from polyaxon._flow.run.kubeflow.pytorch_job import V1PytorchElasticPolicy, V1PytorchJob
from polyaxon._flow.run.kubeflow.replica import V1KFReplica
from polyaxon._flow.run.kubeflow.scheduling_policy import V1SchedulingPolicy
from polyaxon._flow.run.kubeflow.tf_job import V1TFJob
from polyaxon._flow.run.notifier import V1NotifierJob
from polyaxon._flow.run.patch import validate_run_patch
from polyaxon._flow.run.ray import V1RayCluster, V1RayReplica
from polyaxon._flow.run.resources import V1RunResources
from polyaxon._flow.run.service import V1Service
from polyaxon._flow.run.tuner import V1TunerJob

V1Runtime = Annotated[
    Union[
        V1Job,
        V1Service,
        V1Dag,
        V1MPIJob,
        V1PytorchJob,
        V1TFJob,
        V1DaskCluster,
        V1RayCluster,
        V1NotifierJob,
        V1CleanerJob,
        V1TunerJob,
    ],
    Field(discriminator="kind"),
]


class RunMixin:
    def get_replica_types(self):
        raise NotImplementedError

    def get_run_kind(self):
        raise NotImplementedError

    @property
    def is_job_run(self):
        return self.get_run_kind() == V1RunKind.JOB

    @property
    def is_service_run(self):
        return self.get_run_kind() == V1RunKind.SERVICE

    @property
    def is_mpi_job_run(self):
        return self.get_run_kind() == V1RunKind.MPIJOB

    @property
    def is_pytorch_job_run(self):
        return self.get_run_kind() == V1RunKind.PYTORCHJOB

    @property
    def is_tf_job_run(self):
        return self.get_run_kind() == V1RunKind.TFJOB

    @property
    def is_ray_cluster_run(self):
        return self.get_run_kind() == V1RunKind.RAYCLUSTER

    @property
    def is_dask_cluster_run(self):
        return self.get_run_kind() == V1RunKind.DASKCLUSTER

    @property
    def is_dag_run(self):
        return self.get_run_kind() == V1RunKind.DAG

    @property
    def is_schedule_run(self):
        return self.get_run_kind() == V1RunKind.SCHEDULE

    @property
    def is_notifier_run(self):
        return self.get_run_kind() == V1RunKind.NOTIFIER

    @property
    def is_cleaner_run(self):
        return self.get_run_kind() == V1RunKind.CLEANER

    @property
    def is_tuner_run(self):
        return self.get_run_kind() == V1RunKind.TUNER

    @property
    def is_watchdog(self):
        return self.get_run_kind() == V1RunKind.WATCHDOG

    @property
    def is_distributed_run(self):
        return (
            self.is_mpi_job_run
            or self.is_pytorch_job_run
            or self.is_tf_job_run
            or self.is_ray_cluster_run
            or self.is_dask_cluster_run
        )
