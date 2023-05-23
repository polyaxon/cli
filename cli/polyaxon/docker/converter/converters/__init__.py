from polyaxon.docker.converter.converters.job import JobConverter
from polyaxon.docker.converter.converters.service import ServiceConverter
from polyaxon.polyflow import V1RunKind

CONVERTERS = {
    V1RunKind.JOB: JobConverter,
    V1RunKind.SERVICE: ServiceConverter,
}
