from collections.abc import Mapping
from typing import Dict, List, Optional

from clipped.compact.pydantic import ValidationError
from clipped.config.patch_strategy import PatchStrategy
from polyaxon._flow.run.cleaner import V1CleanerJob
from polyaxon._flow.run.dag import V1Dag
from polyaxon._flow.run.dask import V1DaskCluster, V1DaskReplica
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.job import V1Job
from polyaxon._flow.run.kubeflow.mpi_job import V1MPIJob
from polyaxon._flow.run.kubeflow.pytorch_job import V1PytorchJob
from polyaxon._flow.run.kubeflow.replica import V1KFReplica
from polyaxon._flow.run.kubeflow.tf_job import V1TFJob
from polyaxon._flow.run.notifier import V1NotifierJob
from polyaxon._flow.run.ray import V1RayCluster, V1RayReplica
from polyaxon._flow.run.service import V1Service
from polyaxon._flow.run.tuner import V1TunerJob
from polyaxon.exceptions import PolyaxonValidationError


def patch_run(current, value, strategy: Optional[PatchStrategy] = None, base=None):
    strategy = strategy or PatchStrategy.POST_MERGE
    if isinstance(current, Mapping):
        if base is None:
            raise PolyaxonValidationError(
                "Resolve the referenced runtime before merging native run patches."
            )
        # Merge only the local fields; inherited fields stay in component.run.
        current = type(base)().patch(
            validate_run_patch(
                current,
                base.kind,
                replica_types=(
                    base.get_replica_types()
                    if hasattr(base, "get_replica_types")
                    else None
                ),
            )
        )
    if isinstance(value, Mapping):
        runtime = current if current is not None else base
        if runtime is None:
            raise PolyaxonValidationError(
                "run.kind must be provided locally or by a referenced base."
            )
        if base is not None and base.kind == runtime.kind:
            runtime = base
        patch = validate_run_patch(
            value,
            runtime.kind,
            replica_types=(
                runtime.get_replica_types()
                if hasattr(runtime, "get_replica_types")
                else None
            ),
        )
        if current is None:
            return type(runtime)().patch(patch, strategy=strategy)
        return current.patch(patch, strategy=strategy)
    if current is not None and value is not None and current.kind == value.kind:
        return current.patch(value, strategy=strategy)
    if current is None or strategy in (PatchStrategy.POST_MERGE, PatchStrategy.REPLACE):
        return value
    return current


def patch_run_patch(
    current: Optional[Dict],
    value: Optional[Dict],
    kind: Optional[V1RunKind] = None,
    replica_types: Optional[List[str]] = None,
    strategy: Optional[PatchStrategy] = None,
):
    """Merge runtime patches without applying them to the runtime."""
    if value is None:
        return current
    if current is None:
        return value
    if not kind:
        return value if PatchStrategy.is_replace(strategy) else current

    value = validate_run_patch(value, kind, replica_types=replica_types)
    current = validate_run_patch(current, kind, replica_types=replica_types)
    result = current.patch(value, strategy).to_dict()
    result.pop("kind")
    return result


def validate_run_patch(
    run_patch: Dict, kind: V1RunKind, replica_types: List[str] = None
):
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
            if replica_types:
                patch = V1PytorchJob.from_dict({k: run_patch for k in replica_types})
            else:
                patch = V1KFReplica.from_dict(run_patch)
    elif kind == V1RunKind.TFJOB:
        try:
            patch = V1TFJob.from_dict(run_patch)
        except ValidationError:
            if replica_types:
                patch = V1TFJob.from_dict({k: run_patch for k in replica_types})
            else:
                patch = V1KFReplica.from_dict(run_patch)
    elif kind == V1RunKind.RAYCLUSTER:
        try:
            patch = V1RayCluster.from_dict(run_patch)
        except ValidationError:
            if replica_types:
                replicas = {}
                if "head" in replica_types:
                    replicas["head"] = run_patch
                replica_types = [r for r in replica_types if r != "head"]
                replicas["workers"] = {replica: run_patch for replica in replica_types}
                patch = V1RayCluster.from_dict(replicas)
            else:
                patch = V1RayReplica.from_dict(run_patch)
    elif kind == V1RunKind.DASKCLUSTER:
        try:
            patch = V1DaskCluster.from_dict(run_patch)
        except ValidationError:
            if replica_types:
                patch = V1DaskCluster.from_dict({k: run_patch for k in replica_types})
            else:
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
