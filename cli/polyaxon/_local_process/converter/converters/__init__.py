from polyaxon._flow import V1RunKind
from polyaxon._local_process.converter.converters.job import JobConverter
from polyaxon._local_process.converter.converters.service import ServiceConverter

CONVERTERS = {
    V1RunKind.JOB: JobConverter,
    V1RunKind.SERVICE: ServiceConverter,
}
