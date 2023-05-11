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

from polyaxon.auxiliaries import V1PolyaxonInitContainer
from polyaxon.containers.names import INIT_AUTH_CONTAINER
from polyaxon.containers.pull_policy import PullPolicy
from tests.test_docker.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestInitAuth(BaseConverterTest):
    def test_get_auth_context_init_container(self):
        container = self.converter._get_auth_context_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="foo/foo",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            env=[],
        )

        assert container.name == INIT_AUTH_CONTAINER
        assert container.image == "foo/foo"
        assert container.command == ["polyaxon", "initializer", "auth"]
        assert container.args is None
        assert container.env == []
        assert container.resources.to_dict() == {"cpus": "1", "memory": "500Mi"}
        assert container.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=False)
        ]
