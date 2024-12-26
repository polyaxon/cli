from typing import Optional

from polyaxon._schemas.base import BaseSchemaModel


class OperatorsConfig(BaseSchemaModel):
    tfjob: Optional[bool] = None
    pytorchjob: Optional[bool] = None
    paddlejob: Optional[bool] = None
    mpijob: Optional[bool] = None
    mxjob: Optional[bool] = None
    xgbjob: Optional[bool] = None
    daskjob: Optional[bool] = None
    rayjob: Optional[bool] = None
