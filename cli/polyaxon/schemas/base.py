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

from clipped.config.schema import BaseSchemaModel as _BaseSchemaModel

from polyaxon import pkg
from polyaxon.config.spec import ConfigSpec
from polyaxon.exceptions import PolyaxonSchemaError


class BaseSchemaModel(_BaseSchemaModel):
    _VERSION = pkg.SCHEMA_VERSION
    _SCHEMA_EXCEPTION = PolyaxonSchemaError
    _CONFIG_SPEC = ConfigSpec


NAME_REGEX = r"^[-a-zA-Z0-9_]+\Z"
FULLY_QUALIFIED_NAME_REGEX = r"^[-a-zA-Z0-9_]+(:[-a-zA-Z0-9_.]+)?\Z"
