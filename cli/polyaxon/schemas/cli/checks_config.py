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
import os

from datetime import datetime, timedelta
from typing import Optional

from clipped.tz_utils import now

from polyaxon.env_vars.keys import EV_KEYS_INTERVALS_COMPATIBILITY_CHECK
from polyaxon.schemas.base import BaseSchemaModel


class ChecksConfig(BaseSchemaModel):
    _IDENTIFIER = "checks"
    _INTERVAL = 30 * 60

    last_check: Optional[datetime]

    def __init__(
        self,
        last_check=None,
        **data,
    ):
        last_check = self.get_last_check(last_check)
        super().__init__(last_check=last_check, **data)

    def get_interval(self, interval: Optional[int] = None) -> int:
        if interval is not None:
            return interval
        interval = int(
            os.environ.get(EV_KEYS_INTERVALS_COMPATIBILITY_CHECK, self._INTERVAL)
        )
        if interval == -1:
            return interval
        return max(interval, self._INTERVAL)

    @classmethod
    def get_last_check(cls, last_check) -> datetime:
        return last_check or now() - timedelta(cls._INTERVAL)

    def should_check(self, interval: Optional[int] = None) -> bool:
        interval = self.get_interval(interval=interval)
        if interval == -1:
            return False
        if (now() - self.last_check).total_seconds() > interval:
            return True
        return False
