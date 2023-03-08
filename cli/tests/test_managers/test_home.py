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

from polyaxon.managers.home import HomeConfigManager
from polyaxon.schemas.api.home import HomeConfig
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestHomeConfigManager(BaseTestCase):
    def test_default_props(self):
        assert HomeConfigManager.is_global() is True
        assert HomeConfigManager.is_local() is False
        assert HomeConfigManager.IN_POLYAXON_DIR is False
        assert HomeConfigManager.CONFIG_FILE_NAME == ".home"
        assert HomeConfigManager.CONFIG == HomeConfig