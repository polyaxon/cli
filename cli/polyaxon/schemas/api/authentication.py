#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Optional

from pydantic import Extra, Field, StrictStr

from polyaxon.env_vars.keys import EV_KEYS_AUTH_TOKEN, EV_KEYS_AUTH_USERNAME
from polyaxon.schemas.base import BaseSchemaModel


class AccessTokenConfig(BaseSchemaModel):
    """
    Access token config.


    Args:
        username: `str`. The user's username.
        token: `str`. The user's token.
    """

    _IDENTIFIER = "token"

    username: Optional[StrictStr] = Field(alias=EV_KEYS_AUTH_USERNAME)
    token: Optional[StrictStr] = Field(alias=EV_KEYS_AUTH_TOKEN)

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
