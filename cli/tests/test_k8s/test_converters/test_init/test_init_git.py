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
from polyaxon.connections import V1Connection, V1ConnectionKind, V1GitConnection
from polyaxon.containers.names import INIT_GIT_CONTAINER_PREFIX, generate_container_name
from polyaxon.containers.pull_policy import PullPolicy
from polyaxon.contexts import paths as ctx_paths
from polyaxon.exceptions import PolypodException
from polyaxon.k8s.converter.common import constants
from polyaxon.k8s.converter.common.env_vars import (
    get_connection_env_var,
    get_connections_catalog_env_var,
)
from polyaxon.k8s.converter.common.mounts import (
    get_auth_context_mount,
    get_connections_context_mount,
)
from polyaxon.k8s.converter.common.volumes import get_volume_name
from polyaxon.k8s.converter.init.git import (
    get_git_init_container,
    get_repo_context_args,
)
from polyaxon.polyflow import V1Plugins
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.converter_mark
class TestInitGit(BaseTestCase):
    def test_get_repo_context_args_requires_from_image(self):
        with self.assertRaises(PolypodException):
            get_repo_context_args(name=None, url=None, revision=None, mount_path=None)

    def test_get_repo_context_args_with_none_values(self):
        args = get_repo_context_args(
            name="user/repo1",
            url="http://foo.com",
            revision=None,
            mount_path="/somepath",
        )
        assert args == ["--repo-path=/somepath/user/repo1", "--url=http://foo.com"]

    def test_get_repo_context_args(self):
        args = get_repo_context_args(
            name="user/repo1",
            url="http://foo.com",
            revision="00b9d2ea01c40f58d6b4051319f9375675a43c02",
            mount_path="/somepath",
        )
        assert args == [
            "--repo-path=/somepath/user/repo1",
            "--url=http://foo.com",
            "--revision=00b9d2ea01c40f58d6b4051319f9375675a43c02",
        ]

        args = get_repo_context_args(
            name="user/repo1",
            url="http://foo.com",
            revision="dev",
            mount_path="/somepath",
        )
        assert args == [
            "--repo-path=/somepath/user/repo1",
            "--url=http://foo.com",
            "--revision=dev",
        ]

        args = get_repo_context_args(
            name="user/repo1",
            url="http://foo.com",
            revision="00b9d2ea01c40f58d6b4051319f9375675a43c02",
            mount_path="/somepath",
        )
        assert args == [
            "--repo-path=/somepath/user/repo1",
            "--url=http://foo.com",
            "--revision=00b9d2ea01c40f58d6b4051319f9375675a43c02",
        ]

    def test_get_git_init_container_raises_for_missing_info(self):
        with self.assertRaises(PolypodException):
            get_git_init_container(
                polyaxon_init=V1PolyaxonInitContainer(), connection=None, plugins=None
            )

        with self.assertRaises(PolypodException):
            get_git_init_container(
                polyaxon_init=V1PolyaxonInitContainer(image="foo/test"),
                connection=None,
                mount_path=None,
                plugins=None,
            )

    def test_get_git_init_container(self):
        connection = V1Connection(
            name="user/foo",
            kind=V1ConnectionKind.GIT,
            schema_=V1GitConnection(url="foo.com"),
        )
        container = get_git_init_container(
            polyaxon_init=V1PolyaxonInitContainer(image="foo", image_tag=""),
            connection=connection,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
        )
        assert (
            generate_container_name(INIT_GIT_CONTAINER_PREFIX, connection.name, False)
            in container.name
        )
        assert container.image == "foo"
        assert container.image_pull_policy is None
        assert container.command == ["polyaxon", "initializer", "git"]
        assert get_connection_env_var(connection=connection) == []
        assert container.env == [
            get_connections_catalog_env_var(connections=[connection])
        ]
        assert container.resources == get_init_resources()
        assert container.volume_mounts == [
            get_connections_context_mount(
                name=constants.VOLUME_MOUNT_ARTIFACTS,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            ),
            get_auth_context_mount(read_only=True),
        ]

        container = get_git_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init/init",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            connection=connection,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
        )
        assert (
            generate_container_name(INIT_GIT_CONTAINER_PREFIX, connection.name, False)
            in container.name
        )
        assert container.image == "init/init"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["polyaxon", "initializer", "git"]
        assert container.args == [
            "--repo-path={}/{}".format(
                ctx_paths.CONTEXT_MOUNT_ARTIFACTS, connection.name
            ),
            "--url={}".format(connection.schema_.url),
        ]
        assert container.resources == get_init_resources()
        assert container.volume_mounts == [
            get_connections_context_mount(
                name=constants.VOLUME_MOUNT_ARTIFACTS,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            ),
            get_auth_context_mount(read_only=True),
        ]

        connection = V1Connection(
            name="user/foo",
            kind=V1ConnectionKind.GIT,
            schema_=V1GitConnection(
                url="foo.com", revision="00b9d2ea01c40f58d6b4051319f9375675a43c02"
            ),
        )
        container = get_git_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init/init",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            connection=connection,
            mount_path="/somepath",
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
        )
        assert (
            generate_container_name(INIT_GIT_CONTAINER_PREFIX, connection.name, False)
            in container.name
        )
        assert container.image == "init/init"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["polyaxon", "initializer", "git"]
        assert container.args == [
            "--repo-path=/somepath/{}".format(connection.name),
            "--url={}".format(connection.schema_.url),
            "--revision=00b9d2ea01c40f58d6b4051319f9375675a43c02",
        ]
        assert container.resources == get_init_resources()
        assert container.volume_mounts == [
            get_connections_context_mount(
                name=get_volume_name("/somepath"), mount_path="/somepath"
            ),
            get_auth_context_mount(read_only=True),
        ]

        connection = V1Connection(
            name="user/foo",
            kind=V1ConnectionKind.GIT,
            schema_=V1GitConnection(
                url="foo.com",
                revision="00b9d2ea01c40f58d6b4051319f9375675a43c02",
                flags=["--falg1", "--flag2=test", "k=v"],
            ),
        )
        container = get_git_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init/init",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            connection=connection,
            mount_path="/somepath",
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
        )
        assert (
            generate_container_name(INIT_GIT_CONTAINER_PREFIX, connection.name, False)
            in container.name
        )
        assert container.image == "init/init"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["polyaxon", "initializer", "git"]
        assert container.args == [
            "--repo-path=/somepath/{}".format(connection.name),
            "--url={}".format(connection.schema_.url),
            "--revision=00b9d2ea01c40f58d6b4051319f9375675a43c02",
            '--flags=["--falg1","--flag2=test","k=v"]',
        ]
        assert container.resources == get_init_resources()
        assert container.volume_mounts == [
            get_connections_context_mount(
                name=get_volume_name("/somepath"), mount_path="/somepath"
            ),
            get_auth_context_mount(read_only=True),
        ]
