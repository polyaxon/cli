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

from pydantic import ValidationError

from polyaxon.polyflow import V1Cache
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.components_mark
class TestCacheConfigs(BaseTestCase):
    def test_cache_config(self):
        expected_config_dict = {"disable": True}
        assert expected_config_dict == V1Cache.from_dict(expected_config_dict).to_dict()
        config_dict = {"disable": 1}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()
        config_dict = {"disable": "t"}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()

        expected_config_dict = {"disable": False}
        assert expected_config_dict == V1Cache.from_dict(expected_config_dict).to_dict()
        config_dict = {"disable": 0}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()
        config_dict = {"disable": "f"}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()

        expected_config_dict = {
            "io": ["in1", "in2"],
            "sections": ["init", "containers"],
        }
        assert expected_config_dict == V1Cache.from_dict(expected_config_dict).to_dict()

        expected_config_dict = {"disable": True, "ttl": 12, "io": ["in1", "in2"]}
        assert expected_config_dict == V1Cache.from_dict(expected_config_dict).to_dict()
        config_dict = {"disable": 1, "ttl": 12.2, "io": ["in1", "in2"]}
        with self.assertRaises(ValidationError):
            V1Cache.from_dict(config_dict).to_dict()
        config_dict = {"disable": 1, "ttl": "12", "io": ["in1", "in2"]}
        with self.assertRaises(ValidationError):
            V1Cache.from_dict(config_dict)

        expected_config_dict = {"disable": False, "sections": ["containers"]}
        assert expected_config_dict == V1Cache.from_dict(expected_config_dict).to_dict()
        config_dict = {"disable": False, "sections": ("containers",)}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()
        config_dict = {"disable": 0, "sections": ["containers"]}
        assert expected_config_dict == V1Cache.from_dict(config_dict).to_dict()

        with self.assertRaises(ValidationError):
            config_dict = {"disable": "foo"}
            V1Cache.from_dict(config_dict).to_dict()

        with self.assertRaises(ValidationError):
            config_dict = {"ttl": "foo"}
            V1Cache.from_dict(config_dict).to_dict()

        with self.assertRaises(ValidationError):
            config_dict = {"ttl": "12.3"}
            V1Cache.from_dict(config_dict).to_dict()

        with self.assertRaises(ValidationError):
            config_dict = {"sections": ["foo"]}
            V1Cache.from_dict(config_dict).to_dict()

        with self.assertRaises(ValidationError):
            config_dict = {"sections": ["container"]}  # missing s
            V1Cache.from_dict(config_dict).to_dict()
