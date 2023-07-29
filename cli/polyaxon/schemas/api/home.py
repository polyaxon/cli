from typing import Optional

from clipped.compact.pydantic import Extra, Field, StrictStr

from polyaxon.env_vars.keys import EV_KEYS_HOME
from polyaxon.schemas.base import BaseSchemaModel


class HomeConfig(BaseSchemaModel):
    """
    Home config for managing Polyaxon's main context path.


    Args:
        path: `str`. The context path where to write/read configs.
    """

    _IDENTIFIER = "home"

    path: Optional[StrictStr] = Field(alias=EV_KEYS_HOME)

    class Config:
        extra = Extra.ignore
