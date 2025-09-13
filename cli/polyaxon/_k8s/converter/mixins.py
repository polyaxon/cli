from typing import Dict

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
    K8S_ANNOTATIONS_KIND = V1RunKind.JOB
    K8S_LABELS_COMPONENT = "polyaxon-jobs"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class NotifierMixin(BaseMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.NOTIFIER
    K8S_LABELS_COMPONENT = "polyaxon-notifiers"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class CleanerMixin(BaseMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.CLEANER
    K8S_LABELS_COMPONENT = "polyaxon-cleaners"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class TunerMixin(BaseMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.TUNER
    K8S_LABELS_COMPONENT = "polyaxon-tuners"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class ServiceMixin(BaseMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.SERVICE
    K8S_LABELS_COMPONENT = "polyaxon-services"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class TFJobMixin(BaseMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.TFJOB
    K8S_LABELS_COMPONENT = "polyaxon-tfjobs"
    MAIN_CONTAINER_ID = TFJOBS_CONTAINER


class PytorchJobMixin(BaseMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.PYTORCHJOB
    K8S_LABELS_COMPONENT = "polyaxon-pytorch-jobs"
    MAIN_CONTAINER_ID = PYTORCHJOBS_CONTAINER


class MPIJobMixin(BaseMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.MPIJOB
    K8S_LABELS_COMPONENT = "polyaxon-mpi-jobs"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class RayJobMixin(BaseMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.RAYJOB
    K8S_LABELS_COMPONENT = "polyaxon-ray-jobs"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class DaskJobMixin(BaseMixin):
    K8S_ANNOTATIONS_KIND = V1RunKind.DASKJOB
    K8S_LABELS_COMPONENT = "polyaxon-dask-jobs"
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


MIXIN_MAPPING: Dict = {
    V1RunKind.JOB: JobMixin,
    V1RunKind.NOTIFIER: NotifierMixin,
    V1RunKind.CLEANER: CleanerMixin,
    V1RunKind.TUNER: TunerMixin,
    V1RunKind.SERVICE: ServiceMixin,
    V1RunKind.TFJOB: TFJobMixin,
    V1RunKind.PYTORCHJOB: PytorchJobMixin,
    V1RunKind.MPIJOB: MPIJobMixin,
    V1RunKind.RAYJOB: RayJobMixin,
    V1RunKind.DASKJOB: DaskJobMixin,
}
