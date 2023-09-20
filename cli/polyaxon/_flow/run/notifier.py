from typing_extensions import Literal

from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.job import V1Job


class V1NotifierJob(V1Job):
    _IDENTIFIER = V1RunKind.NOTIFIER

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
