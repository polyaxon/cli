from polyaxon._docker.converter.converters.job import JobConverter
from polyaxon._docker.converter.converters.service import ServiceConverter
from polyaxon._flow import V1RunKind

CONVERTERS = {
    V1RunKind.JOB: JobConverter,
    V1RunKind.SERVICE: ServiceConverter,
}
