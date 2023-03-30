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

from pydantic import StrictStr

from polyaxon.schemas.types.base import BaseTypeConfig


class V1AuthType(BaseTypeConfig):
    """Auth type.

    Args:
        user: str
        password: str

    ### YAML usage

    The inputs definition

    ```yaml
    >>> inputs:
    >>>   - name: test1
    >>>     type: auth
    >>>   - name: test2
    >>>     type: auth
    ```

    The params usage

    ```yaml
    >>> params:
    >>>   test1: {value: "username1:password1"}
    >>>   test1: {value: {"user": "username2", "password": "password2"}}
    ```

    ### Python usage

    The inputs definition

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import types
    >>> from polyaxon.polyflow import V1IO
    >>> inputs = [
    >>>     V1IO(
    >>>         name="test1",
    >>>         type=types.AUTH,
    >>>     ),
    >>>     V1IO(
    >>>         name="test2",
    >>>         type=types.AUTH,
    >>>     ),
    >>> ]
    ```

    The params usage

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import types
    >>> from polyaxon.polyflow import V1Param
    >>> params = {
    >>>     "test1": V1Param(value=types.V1AuthType(user="username1", password="password1")),
    >>>     "test2": V1Param(value=types.V1AuthType(user="username2", password="password2")),
    >>> }
    ```

    > Normally you should not be passing auth details in plain values.

    This type validate several values:

    String values:
       * '{"user": "foo", "password": "bar"}'
       * 'foo:bar'

    Dict values:
       * {"user": "foo", "password": "bar"}
    """

    _IDENTIFIER = "auth"

    user: StrictStr
    password: StrictStr

    def __str__(self):
        return "{}:{}".format(self.user, self.password)

    def __repr__(self):
        return str(self)
