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

from polyaxon.auxiliaries import V1PolyaxonInitContainer, get_init_resources
from polyaxon.containers.names import INIT_FILE_CONTAINER_PREFIX
from polyaxon.containers.pull_policy import PullPolicy
from polyaxon.contexts import paths as ctx_paths
from polyaxon.converter.init.file import get_file_init_container
from polyaxon.k8s import constants
from polyaxon.k8s.mounts import get_auth_context_mount, get_connections_context_mount
from polyaxon.polyflow import V1Plugins
from polyaxon.schemas.types import V1FileType
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.converter_mark
class TestInitFile(BaseTestCase):
    def test_get_file_init_container(self):
        file_args = V1FileType(content="test")
        container = get_file_init_container(
            polyaxon_init=V1PolyaxonInitContainer(image="foo", image_tag=""),
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            file_args=file_args,
            run_path="test",
            run_instance="foo.bar.runs.uuid",
        )
        assert INIT_FILE_CONTAINER_PREFIX in container.name
        assert container.image == "foo"
        assert container.image_pull_policy is None
        assert container.command == ["polyaxon", "initializer", "file"]
        assert container.resources == get_init_resources()
        assert container.volume_mounts == [
            get_connections_context_mount(
                name=constants.VOLUME_MOUNT_ARTIFACTS,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            ),
            get_auth_context_mount(read_only=True),
        ]
        assert file_args.to_json() == '{"content":"test","filename":"file"}'
        assert container.args == [
            "--file-context={}".format('{"content":"test","filename":"file"}'),
            "--filepath={}".format(ctx_paths.CONTEXT_MOUNT_ARTIFACTS),
            "--copy-path={}".format(
                ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format("test")
            ),
            "--track",
        ]

        file_args = V1FileType(filename="test", content="test")
        container = get_file_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init/init",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            file_args=file_args,
            run_path="test",
            run_instance="foo.bar.runs.uuid",
        )
        assert INIT_FILE_CONTAINER_PREFIX in container.name
        assert container.image == "init/init"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["polyaxon", "initializer", "file"]
        assert container.args == [
            "--file-context={}".format(file_args.to_json()),
            "--filepath={}".format(ctx_paths.CONTEXT_MOUNT_ARTIFACTS),
            "--copy-path={}".format(
                ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format("test")
            ),
            "--track",
        ]
        assert container.resources == get_init_resources()
        assert container.volume_mounts == [
            get_connections_context_mount(
                name=constants.VOLUME_MOUNT_ARTIFACTS,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            ),
            get_auth_context_mount(read_only=True),
        ]
