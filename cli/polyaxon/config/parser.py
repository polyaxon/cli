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
from clipped.config.parser import Parser as _Parser
from clipped.decorators.memoization import memoize

from polyaxon.exceptions import PolyaxonSchemaError


class Parser(_Parser):
    _SCHEMA_EXCEPTION = PolyaxonSchemaError

    @staticmethod
    @memoize
    def type_mapping():
        from polyaxon import types

        return types.MAPPING

    @staticmethod
    @memoize
    def type_forwarding():
        from polyaxon import types

        return types.FORWARDING
