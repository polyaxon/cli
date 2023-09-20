from typing import Dict

from clipped.compact.pydantic import ValidationError

from polyaxon._flow.run.cleaner import V1CleanerJob
from polyaxon._flow.run.dag import V1Dag
from polyaxon._flow.run.dask import V1DaskJob, V1DaskReplica
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.job import V1Job
from polyaxon._flow.run.kubeflow.mpi_job import V1MPIJob
from polyaxon._flow.run.kubeflow.mx_job import V1MXJob
from polyaxon._flow.run.kubeflow.paddle_job import V1PaddleJob
from polyaxon._flow.run.kubeflow.pytorch_job import V1PytorchJob
from polyaxon._flow.run.kubeflow.replica import V1KFReplica
from polyaxon._flow.run.kubeflow.tf_job import V1TFJob
from polyaxon._flow.run.kubeflow.xgboost_job import V1XGBoostJob
from polyaxon._flow.run.notifier import V1NotifierJob
from polyaxon._flow.run.ray import V1RayJob, V1RayReplica
from polyaxon._flow.run.service import V1Service
from polyaxon._flow.run.tuner import V1TunerJob
from polyaxon.exceptions import PolyaxonValidationError


def validate_run_patch(run_patch: Dict, kind: V1RunKind):
    if kind == V1RunKind.JOB:
        patch = V1Job.from_dict(run_patch)
    elif kind == V1RunKind.SERVICE:
        patch = V1Service.from_dict(run_patch)
    elif kind == V1RunKind.DAG:
        patch = V1Dag.from_dict(run_patch)
    elif kind == V1RunKind.MPIJOB:
        try:
            patch = V1MPIJob.from_dict(run_patch)
        except ValidationError:
            patch = V1KFReplica.from_dict(run_patch)
    elif kind == V1RunKind.PYTORCHJOB:
        try:
            patch = V1PytorchJob.from_dict(run_patch)
        except ValidationError:
            patch = V1KFReplica.from_dict(run_patch)
    elif kind == V1RunKind.PADDLEJOB:
        try:
            patch = V1PaddleJob.from_dict(run_patch)
        except ValidationError:
            patch = V1KFReplica.from_dict(run_patch)
    elif kind == V1RunKind.TFJOB:
        try:
            patch = V1TFJob.from_dict(run_patch)
        except ValidationError:
            patch = V1KFReplica.from_dict(run_patch)
    elif kind == V1RunKind.MXJOB:
        try:
            patch = V1MXJob.from_dict(run_patch)
        except ValidationError:
            patch = V1KFReplica.from_dict(run_patch)
    elif kind == V1RunKind.XGBJOB:
        try:
            patch = V1XGBoostJob.from_dict(run_patch)
        except ValidationError:
            patch = V1KFReplica.from_dict(run_patch)
    elif kind == V1RunKind.RAYJOB:
        try:
            patch = V1RayJob.from_dict(run_patch)
        except ValidationError:
            patch = V1RayReplica.from_dict(run_patch)
    elif kind == V1RunKind.DASKJOB:
        try:
            patch = V1DaskJob.from_dict(run_patch)
        except ValidationError:
            patch = V1DaskReplica.from_dict(run_patch)
    elif kind == V1RunKind.NOTIFIER:
        patch = V1NotifierJob.from_dict(run_patch)
    elif kind == V1RunKind.TUNER:
        patch = V1TunerJob.from_dict(run_patch)
    elif kind == V1RunKind.CLEANER:
        patch = V1CleanerJob.from_dict(run_patch)
    else:
        raise PolyaxonValidationError(
            "runPatch cannot be validate without a supported kind."
        )

    return patch
