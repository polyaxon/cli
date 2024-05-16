from typing import Dict

from polyaxon._containers.names import MAIN_JOB_CONTAINER
from polyaxon._flow import V1RunKind


class JobMixin:
    K8S_ANNOTATIONS_KIND = V1RunKind.JOB
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class NotifierMixin:
    K8S_ANNOTATIONS_KIND = V1RunKind.NOTIFIER
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class CleanerMixin:
    K8S_ANNOTATIONS_KIND = V1RunKind.CLEANER
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class TunerMixin:
    K8S_ANNOTATIONS_KIND = V1RunKind.TUNER
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


class ServiceMixin:
    K8S_ANNOTATIONS_KIND = V1RunKind.SERVICE
    MAIN_CONTAINER_ID = MAIN_JOB_CONTAINER


MIXIN_MAPPING: Dict = {
    V1RunKind.JOB: JobMixin,
    V1RunKind.NOTIFIER: NotifierMixin,
    V1RunKind.CLEANER: CleanerMixin,
    V1RunKind.TUNER: TunerMixin,
    V1RunKind.SERVICE: ServiceMixin,
}
