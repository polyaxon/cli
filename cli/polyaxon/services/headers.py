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
from typing import Tuple

from polyaxon.utils.enums_utils import PEnum, get_enum_value


class PolyaxonServiceHeaders(str, PEnum):
    CLI_VERSION = "X_POLYAXON_CLI_VERSION"
    CLIENT_VERSION = "X_POLYAXON_CLIENT_VERSION"
    INTERNAL = "X_POLYAXON_INTERNAL"
    SERVICE = "X_POLYAXON_SERVICE"

    @staticmethod
    def get_header(header) -> str:
        return get_enum_value(header).replace("_", "-")

    @classmethod
    def get_headers(cls) -> Tuple[str]:
        return tuple(cls.to_set() | {cls.get_header(h) for h in cls.to_set()})
