#!/usr/bin/python
#
# Copyright 2018-2021 Polyaxon, Inc.
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

from polyaxon.schemas.api.user import UserConfig
from tests.utils import BaseTestCase


@pytest.mark.api_mark
class TestUserConfigs(BaseTestCase):
    def test_user_config(self):
        config_dict = {
            "username": "username",
            "email": "user@domain.com",
            "name": "foo bat",
            "theme": 1,
        }
        config = UserConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict
