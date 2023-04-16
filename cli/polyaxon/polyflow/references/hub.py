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
from typing_extensions import Literal

from pydantic import StrictStr

from polyaxon.polyflow.references.mixin import RefMixin
from polyaxon.schemas.base import BaseSchemaModel


class V1HubRef(BaseSchemaModel, RefMixin):
    _IDENTIFIER = "hub_ref"
    _USE_DISCRIMINATOR = True

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    name: StrictStr

    def get_kind_value(self):
        return self.name
