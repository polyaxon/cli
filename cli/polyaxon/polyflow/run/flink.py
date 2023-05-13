from typing import Dict, Union
from typing_extensions import Literal

from clipped.types.ref_or_obj import RefField

from polyaxon.polyflow.run.base import BaseRun
from polyaxon.polyflow.run.kinds import V1RunKind


class V1Flink(BaseRun):
    _IDENTIFIER = V1RunKind.FLINK

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    spec: Union[Dict, RefField]
