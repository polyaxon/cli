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

from polyaxon.client import PolyaxonClient
from polyaxon.runner.agent import BaseAgent
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.agent_mark
class TestBaseAgent(BaseTestCase):
    SET_AGENT_SETTINGS = True

    def test_init_base_agent(self):
        agent = BaseAgent()
        assert agent.sleep_interval is None
        assert agent.executor is None
        assert isinstance(agent.client, PolyaxonClient)

        agent = BaseAgent(sleep_interval=2)
        assert agent.sleep_interval == 2
        assert agent.executor is None
        assert isinstance(agent.client, PolyaxonClient)
