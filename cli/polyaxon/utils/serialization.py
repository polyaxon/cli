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
from typing import Any

from pydantic.datetime_parse import parse_date, parse_datetime, parse_duration
from pydantic.validators import uuid_validator

date_serialize = lambda x: x.isoformat()
date_deserialize = lambda x: parse_date(x)

datetime_serialize = lambda x: x.isoformat() if x else x
datetime_deserialize = lambda x: parse_datetime(x) if x else x

timedelta_serialize = lambda x: x.total_seconds() if x else x
timedelta_deserialize = lambda x: parse_duration(x) if x else x


class _DummyField:
    type_ = None


_dummy_field: Any = _DummyField()

uuid_serialize = lambda x: x.hex if x else x
uuid_deserialize = lambda x: uuid_validator(x, _dummy_field) if x else x
