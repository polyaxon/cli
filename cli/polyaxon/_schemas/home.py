from typing import Optional

from clipped.compact.pydantic import Extra, Field, StrictStr

from polyaxon._env_vars.keys import ENV_KEYS_HOME
from polyaxon._schemas.base import BaseSchemaModel


class HomeConfig(BaseSchemaModel):
    """
    Home config for managing the main context path.


    Args:
        path: `str`. The context path where to write/read configs.
    """

    _IDENTIFIER = "home"

    path: Optional[StrictStr] = Field(alias=ENV_KEYS_HOME)

    class Config:
        extra = Extra.ignore
