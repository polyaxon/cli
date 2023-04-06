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

from clipped.enums_utils import PEnum

from polyaxon.lifecycle import V1Statuses


class V1TriggerPolicy(str, PEnum):
    ALL_SUCCEEDED = "all_succeeded"
    ALL_FAILED = "all_failed"
    ALL_DONE = "all_done"
    ONE_SUCCEEDED = "one_succeeded"
    ONE_FAILED = "one_failed"
    ONE_DONE = "one_done"

    @classmethod
    def trigger_statuses_mapping(cls):
        return {
            cls.ALL_SUCCEEDED: V1Statuses.SUCCEEDED,
            cls.ALL_FAILED: V1Statuses.FAILED,
            cls.ALL_DONE: V1Statuses.DONE,
            cls.ONE_SUCCEEDED: V1Statuses.SUCCEEDED,
            cls.ONE_FAILED: V1Statuses.FAILED,
            cls.ONE_DONE: V1Statuses.DONE,
        }
