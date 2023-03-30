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

from polyaxon.utils.enums_utils import PEnum


class V1PatchStrategy(str, PEnum):
    REPLACE = "replace"
    ISNULL = "isnull"
    POST_MERGE = "post_merge"
    PRE_MERGE = "pre_merge"

    @classmethod
    def is_replace(cls, value):
        return value == cls.REPLACE

    @classmethod
    def is_null(cls, value):
        return value == cls.ISNULL

    @classmethod
    def is_post_merge(cls, value):
        return value == cls.POST_MERGE

    @classmethod
    def is_pre_merge(cls, value):
        return value == cls.PRE_MERGE
