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

from uuid import uuid4

from polyaxon.polyflow import V1Operation
from polyaxon.utils.fixtures import (
    get_fxt_build_run_pipeline,
    get_fxt_build_run_pipeline_with_inputs,
    get_fxt_map_reduce,
    get_fxt_pipeline_params_env_termination,
    get_fxt_templated_pipeline_with_upstream_run,
    get_fxt_templated_pipeline_without_params,
    get_fxt_train_tensorboard_events_pipeline,
)
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.fixtures_mark
class TestPipelinesFixtures(BaseTestCase):
    def test_fxt_templated_pipeline_without_params(self):
        config = get_fxt_templated_pipeline_without_params()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_templated_pipeline_with_upstream_run(self):
        config = get_fxt_templated_pipeline_with_upstream_run(run_uuid=uuid4())
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_build_run_pipeline(self):
        config = get_fxt_build_run_pipeline()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_train_tensorboard_events_pipeline(self):
        config = get_fxt_train_tensorboard_events_pipeline()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_build_run_pipeline_with_inputs(self):
        config = get_fxt_build_run_pipeline_with_inputs()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_pipeline_params_env_termination(self):
        config = get_fxt_pipeline_params_env_termination()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_map_reduce(self):
        config = get_fxt_map_reduce()
        assert V1Operation.read(config).to_dict() == config
