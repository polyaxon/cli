from polyaxon._flow import V1RunKind
from polyaxon._k8s.converter.converters.dask_job import DaskJobConverter
from polyaxon._k8s.converter.converters.helpers import (
    CleanerConverter,
    NotifierConverter,
    TunerConverter,
)
from polyaxon._k8s.converter.converters.job import JobConverter
from polyaxon._k8s.converter.converters.kubeflow import (
    MPIJobConverter,
    MXJobConverter,
    PaddleJobConverter,
    PytorchJobConverter,
    TfJobConverter,
    XGBoostJobConverter,
)
from polyaxon._k8s.converter.converters.ray_job import RayJobConverter
from polyaxon._k8s.converter.converters.service import ServiceConverter

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
