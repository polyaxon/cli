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

from polyaxon.docker.converter.base import BaseConverter
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.converter_mark
class TestConverter(BaseTestCase):
    def setUp(self):
        class DummyConverter(BaseConverter):
            SPEC_KIND = "dummy"
            MAIN_CONTAINER_ID = "dummy"

        self.converter = DummyConverter(
            owner_name="foo", project_name="p1", run_name="j1", run_uuid="uuid"
        )
        super().setUp()

    def test_is_valid(self):
        class Converter(BaseConverter):
            pass

        with self.assertRaises(PolyaxonConverterError):
            Converter(
                owner_name="foo", project_name="test", run_name="test", run_uuid="uuid"
            )

    def test_run_instance(self):
        assert self.converter.run_instance == "foo.p1.runs.uuid"
