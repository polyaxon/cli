from polyaxon.k8s.converter.converters.dask_job import DaskJobConverter
from polyaxon.k8s.converter.converters.helpers import (
    CleanerConverter,
    NotifierConverter,
    TunerConverter,
)
from polyaxon.k8s.converter.converters.job import JobConverter
from polyaxon.k8s.converter.converters.kubeflow import (
    MPIJobConverter,
    MXJobConverter,
    PaddleJobConverter,
    PytorchJobConverter,
    TfJobConverter,
    XGBoostJobConverter,
)
from polyaxon.k8s.converter.converters.ray_job import RayJobConverter
from polyaxon.k8s.converter.converters.service import ServiceConverter
from polyaxon.polyflow import V1RunKind

CONVERTERS = {
    V1RunKind.CLEANER: CleanerConverter,
    V1RunKind.NOTIFIER: NotifierConverter,
    V1RunKind.TUNER: TunerConverter,
    V1RunKind.JOB: JobConverter,
    V1RunKind.SERVICE: ServiceConverter,
    V1RunKind.MPIJOB: MPIJobConverter,
    V1RunKind.TFJOB: TfJobConverter,
    V1RunKind.PADDLEJOB: PaddleJobConverter,
    V1RunKind.PYTORCHJOB: PytorchJobConverter,
    V1RunKind.MXJOB: MXJobConverter,
    V1RunKind.XGBJOB: XGBoostJobConverter,
    V1RunKind.RAYJOB: RayJobConverter,
    V1RunKind.DASKJOB: DaskJobConverter,
}
