from typing import Dict, Optional

from polyaxon._containers.names import (
    MAIN_JOB_CONTAINER,
    PYTORCHJOBS_CONTAINER,
    TFJOBS_CONTAINER,
)
from polyaxon._flow import V1RunKind
from polyaxon._k8s.custom_resources import operation


class BaseMixin:
    SPEC_KIND = operation.KIND
    API_VERSION = operation.API_VERSION
    PLURAL = operation.PLURAL
    GROUP = operation.GROUP
    K8S_LABELS_PART_OF = "polyaxon-runs"


class JobMixin(BaseMixin):
    SPEC_KIND = operation.JOB_KIND
    PLURAL = operation.JOB_PLURAL
    K8S_ANNOTATIONS_KIND = V1RunKind.JOB
    K8S_LABELS_COMPONENT = "polyaxon-jobs"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class NotifierMixin(JobMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.NOTIFIER
    K8S_LABELS_COMPONENT = "polyaxon-notifiers"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class CleanerMixin(JobMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.CLEANER
    K8S_LABELS_COMPONENT = "polyaxon-cleaners"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class TunerMixin(JobMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.TUNER
    K8S_LABELS_COMPONENT = "polyaxon-tuners"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class ServiceMixin(BaseMixin):
    SPEC_KIND = operation.SERVICES_KIND
    PLURAL = operation.SERVICES_PLURAL
    K8S_ANNOTATIONS_KIND = V1RunKind.SERVICE
    K8S_LABELS_COMPONENT = "polyaxon-services"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class TFJobMixin(BaseMixin):
    SPEC_KIND = operation.KFJOB_KIND
    PLURAL = operation.KFJOB_PLURAL
    K8S_ANNOTATIONS_KIND = V1RunKind.TFJOB
    K8S_LABELS_COMPONENT = "polyaxon-tfjobs"
    MAIN_CONTAINER_ID = TFJOBS_CONTAINER


class PytorchJobMixin(BaseMixin):
    SPEC_KIND = operation.KFJOB_KIND
    PLURAL = operation.KFJOB_PLURAL
    K8S_ANNOTATIONS_KIND = V1RunKind.PYTORCHJOB
    K8S_LABELS_COMPONENT = "polyaxon-pytorch-jobs"
    MAIN_CONTAINER_ID = PYTORCHJOBS_CONTAINER


class MPIJobMixin(BaseMixin):
    SPEC_KIND = operation.KFJOB_KIND
    PLURAL = operation.KFJOB_PLURAL
    K8S_ANNOTATIONS_KIND = V1RunKind.MPIJOB
    K8S_LABELS_COMPONENT = "polyaxon-mpi-jobs"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class RayClusterMixin(BaseMixin):
    SPEC_KIND = operation.CLUSTER_KIND
    PLURAL = operation.CLUSTER_PLURAL
    K8S_ANNOTATIONS_KIND = V1RunKind.RAYCLUSTER
    K8S_LABELS_COMPONENT = "polyaxon-ray-clusters"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class DaskClusterMixin(BaseMixin):
    SPEC_KIND = operation.CLUSTER_KIND
    PLURAL = operation.CLUSTER_PLURAL
    K8S_ANNOTATIONS_KIND = V1RunKind.DASKCLUSTER
    K8S_LABELS_COMPONENT = "polyaxon-dask-clusters"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


def get_plural_for_kind(kind: Optional[V1RunKind]) -> str:
    if not kind:
        return operation.PLURAL
    mixin = MIXIN_MAPPING.get(kind)
    if mixin:
        return mixin.PLURAL
    return operation.PLURAL


MIXIN_MAPPING: Dict = {
    V1RunKind.JOB: JobMixin,
    V1RunKind.NOTIFIER: NotifierMixin,
    V1RunKind.CLEANER: CleanerMixin,
    V1RunKind.TUNER: TunerMixin,
    V1RunKind.SERVICE: ServiceMixin,
    V1RunKind.TFJOB: TFJobMixin,
    V1RunKind.PYTORCHJOB: PytorchJobMixin,
    V1RunKind.MPIJOB: MPIJobMixin,
    V1RunKind.RAYCLUSTER: RayClusterMixin,
    V1RunKind.DASKCLUSTER: DaskClusterMixin,
}
