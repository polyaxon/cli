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
import pytest

from polyaxon.polyflow import V1Operation
from polyaxon.utils.fixtures import get_fxt_schedule_with_inputs_outputs
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.fixtures_mark
class TestSchedulesFixtures(BaseTestCase):
    def test_fxt_schedule_with_inputs_outputs(self):
        config = get_fxt_schedule_with_inputs_outputs()
        assert V1Operation.read(config).to_dict() == config
