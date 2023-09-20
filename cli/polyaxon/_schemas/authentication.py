from typing import Optional

from clipped.compact.pydantic import Extra, Field, StrictStr

from polyaxon._env_vars.keys import ENV_KEYS_AUTH_TOKEN, ENV_KEYS_AUTH_USERNAME
from polyaxon._schemas.base import BaseSchemaModel


class AccessTokenConfig(BaseSchemaModel):
    """
    Access token config.


    Args:
        username: `str`. The user's username.
        token: `str`. The user's token.
    """

    _IDENTIFIER = "token"

    username: Optional[StrictStr] = Field(alias=ENV_KEYS_AUTH_USERNAME)
    token: Optional[StrictStr] = Field(alias=ENV_KEYS_AUTH_TOKEN)

    class Config:
        extra = Extra.ignore


class V1Credentials(BaseSchemaModel):
    """
    Credentials config.


    Args:
        username: `str`. The user's username.
        password: `str`. The user's password.
    """

    _IDENTIFIER = "credentials"

    username: StrictStr
    password: StrictStr
