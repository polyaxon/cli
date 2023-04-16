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
from typing import List, Optional, Union

from clipped.types.ref_or_obj import BoolOrRef, RefField
from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1Template(BaseSchemaModel):
    """A template is way for users to define
    specifications (components/operations) and signal to the CLI/API
    that they are not executable without modification.

    Oftentimes, a user might create a component or an operation that depends on a connection,
    if the user decides to share this specification they will have to face two choices:
     * Remove the connection, other users will be wondering why the specification does not work.
     * Leave the connection, other users will only know about
       the error after they execute the specification.

    By setting the template section, users can signal that this is not executable,
    and if a user runs the specification accidentally,
    they will be shown an error that gets augmented by instruction from the template's description,
    and optionally the fields that need to be modifier.

    Args:
        enabled: bool, optional
        description: str, optional
        fields: List[str], optional

    ## YAML usage

    ```yaml
    >>> template:
    >>>   enabled: true
    >>>   description:
    >>>   fields:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.polyflow import V1Template
    >>> template = V1Template(
    >>>     enabled=True,
    >>>     description="This operation cannot be executed and requires proper annotations.",
    >>>     fields=["environment.annotations", "environment.labels"],
    >>> )
    ```

    ## Fields

    ### enabled

    A flag to enable the template behavior.

    ```yaml
    >>> template:
    >>>   enabled: true
    ```

    ### description

    An optional description about the template.
    The description is also helpful to extend the error raised by the CLI/API.

    ```yaml
    >>> template:
    >>>   description: "some more information about why this is a template and how to execute it"
    ```

    ### fields

    An optional list of field paths that need to be customized to run the specification.

    ```yaml
    >>> template:
    >>>   fields: ["environment.annotations", "environment.labels"]
    ```
    """

    _IDENTIFIER = "template"

    enabled: Optional[BoolOrRef]
    description: Optional[StrictStr]
    fields: Optional[Union[List[StrictStr], RefField]]


class TemplateMixinConfig:
    def disable_template(self):
        if self.is_template():
            self.template.enabled = False

    def is_template(self):
        return self.template and self.template.enabled
