from typing_extensions import Literal

from polyaxon.polyflow.run.enums import V1RunKind
from polyaxon.polyflow.run.job import V1Job


class V1CleanerJob(V1Job):
    _IDENTIFIER = V1RunKind.CLEANER

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
