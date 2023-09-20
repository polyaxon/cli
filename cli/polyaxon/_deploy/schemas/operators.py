from typing import Optional

from polyaxon._schemas.base import BaseSchemaModel


class OperatorsConfig(BaseSchemaModel):
    tfjob: Optional[bool]
    pytorchjob: Optional[bool]
    paddlejob: Optional[bool]
    mpijob: Optional[bool]
    mxjob: Optional[bool]
    xgbjob: Optional[bool]
    daskjob: Optional[bool]
    rayjob: Optional[bool]
