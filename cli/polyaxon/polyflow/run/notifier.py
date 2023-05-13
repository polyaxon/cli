from typing_extensions import Literal

from polyaxon.polyflow.run.job import V1Job
from polyaxon.polyflow.run.kinds import V1RunKind


class V1NotifierJob(V1Job):
    _IDENTIFIER = V1RunKind.NOTIFIER

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
