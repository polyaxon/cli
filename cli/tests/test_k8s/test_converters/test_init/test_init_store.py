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

import os
import pytest

from polyaxon.auxiliaries import V1PolyaxonInitContainer, get_init_resources
from polyaxon.connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1ConnectionResource,
)
from polyaxon.containers.names import (
    INIT_ARTIFACTS_CONTAINER_PREFIX,
    generate_container_name,
)
from polyaxon.containers.pull_policy import PullPolicy
from polyaxon.contexts import paths as ctx_paths
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.common.env_vars import (
    get_connection_env_var,
    get_connections_catalog_env_var,
    get_env_var,
    get_items_from_secret,
)
from polyaxon.k8s.converter.common.mounts import (
    get_connections_context_mount,
    get_mount_from_resource,
    get_mount_from_store,
)
from polyaxon.k8s.converter.common.volumes import get_volume_name
from polyaxon.runner.converter.common import constants
from polyaxon.runner.converter.init.store import get_volume_args
from tests.test_k8s.test_converters.test_init.base import BaseTestInit


@pytest.mark.converter_mark
class TestInitStore(BaseTestInit):
    def test_get_base_store_container_with_none_values(self):
        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_base_store_container(
                container=k8s_schemas.V1Container(name="init"),
                container_name=None,
                polyaxon_init=V1PolyaxonInitContainer(),
                store=None,
                env=None,
                env_from=None,
                volume_mounts=None,
                args=None,
            )

    def test_get_base_store_container_with_store_without_secret(self):
        bucket_store_without_secret = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
        )
        container = self.converter._get_base_store_container(
            container=k8s_schemas.V1Container(name="test"),
            container_name="init",
            polyaxon_init=V1PolyaxonInitContainer(image_tag=""),
            store=bucket_store_without_secret,
            env=None,
            env_from=None,
            volume_mounts=None,
            args=None,
        )

        assert container.name == "init"
        assert container.image == "polyaxon/polyaxon-init"
        assert container.image_pull_policy is None
        assert container.command == ["/bin/sh", "-c"]
        assert container.args is None
        assert get_connection_env_var(connection=bucket_store_without_secret) == []
        assert container.env == [
            get_connections_catalog_env_var(connections=[bucket_store_without_secret])
        ]
        assert container.env_from == []
        assert container.resources is not None
        assert container.volume_mounts == []

    def test_get_base_store_container_with_store_with_secret(self):
        non_mount_resource1 = V1ConnectionResource(
            name="ref",
            items=["item1", "item2"],
            is_requested=False,
        )
        bucket_store_with_secret = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
            secret=non_mount_resource1,
        )
        container = self.converter._get_base_store_container(
            container=k8s_schemas.V1Container(name="init"),
            container_name="init",
            polyaxon_init=V1PolyaxonInitContainer(image_tag=""),
            store=bucket_store_with_secret,
            env=None,
            env_from=None,
            volume_mounts=None,
            args=None,
        )
        assert container.name == "init"
        assert container.image == "polyaxon/polyaxon-init"
        assert container.image_pull_policy is None
        assert container.command == ["/bin/sh", "-c"]
        assert container.args is None

        assert get_connection_env_var(connection=bucket_store_with_secret) == []
        assert container.env == get_items_from_secret(secret=non_mount_resource1) + [
            get_connections_catalog_env_var(connections=[bucket_store_with_secret])
        ]
        assert container.env_from == []
        assert container.resources is not None
        assert container.volume_mounts == []

        mount_resource1 = V1ConnectionResource(
            name="resource",
            items=["item1", "item2"],
            mount_path="/tmp1",
            is_requested=False,
        )
        bucket_store_with_secret.secret = mount_resource1
        container = self.converter._get_base_store_container(
            container=k8s_schemas.V1Container(name="init"),
            container_name="init",
            polyaxon_init=V1PolyaxonInitContainer(image_tag=""),
            store=bucket_store_with_secret,
            env=None,
            env_from=None,
            volume_mounts=None,
            args=None,
        )
        assert container.name == "init"
        assert container.image == "polyaxon/polyaxon-init"
        assert container.image_pull_policy is None
        assert container.command == ["/bin/sh", "-c"]
        assert container.args is None
        assert get_connection_env_var(connection=bucket_store_with_secret) == []
        assert container.env == [
            get_connections_catalog_env_var(connections=[bucket_store_with_secret])
        ]
        assert container.env_from == []
        assert container.resources is not None
        assert container.volume_mounts == [
            get_mount_from_resource(resource=mount_resource1)
        ]

    def test_get_base_store_container_with_mount_store(self):
        claim_store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )

        container = self.converter._get_base_store_container(
            container=k8s_schemas.V1Container(name="init"),
            container_name="init",
            polyaxon_init=V1PolyaxonInitContainer(image_tag=""),
            store=claim_store,
            env=None,
            env_from=None,
            volume_mounts=None,
            args=None,
        )
        assert container.name == "init"
        assert container.image == "polyaxon/polyaxon-init"
        assert container.image_pull_policy is None
        assert container.command == ["/bin/sh", "-c"]
        assert container.args is None
        assert get_connection_env_var(connection=claim_store) == []
        assert container.env == [
            get_connections_catalog_env_var(connections=[claim_store])
        ]
        assert container.env_from == []
        assert container.resources is not None
        assert container.volume_mounts == [get_mount_from_store(store=claim_store)]

    def test_get_base_container(self):
        store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )
        env = [get_env_var(name="key", value="value")]
        env_from = [k8s_schemas.V1EnvFromSource(secret_ref={"name": "ref"})]
        mounts = [k8s_schemas.V1VolumeMount(name="test", mount_path="/test")]
        container = self.converter._get_base_store_container(
            container=k8s_schemas.V1Container(name="init"),
            container_name="init",
            polyaxon_init=V1PolyaxonInitContainer(
                image="foo/foo",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            store=store,
            env=env,
            env_from=env_from,
            volume_mounts=mounts,
            args=["test"],
        )
        assert container.name == "init"
        assert container.image == "foo/foo"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["/bin/sh", "-c"]
        assert container.args == ["test"]
        assert container.env == env
        assert container.env_from == env_from
        assert container.resources is not None
        assert container.volume_mounts == mounts + [get_mount_from_store(store=store)]

    def test_get_store_container_mount_stores(self):
        # Managed store
        store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )
        container = self.converter._get_store_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="foo/foo",
                image_tag="foo",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            connection=store,
            artifacts=None,
            paths=None,
        )
        mount_path = ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(store.name)
        assert (
            generate_container_name(INIT_ARTIFACTS_CONTAINER_PREFIX, store.name, False)
            in container.name
        )
        assert container.image == "foo/foo:foo"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["/bin/sh", "-c"]
        assert container.args == [
            get_volume_args(
                store=store, mount_path=mount_path, artifacts=None, paths=None
            )
        ]
        assert get_connection_env_var(connection=store) == []
        assert container.env == [get_connections_catalog_env_var(connections=[store])]
        assert container.env_from == []
        assert container.resources is not None
        assert container.volume_mounts == [
            get_connections_context_mount(
                name=constants.VOLUME_MOUNT_ARTIFACTS,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            ),
            get_mount_from_store(store=store),
        ]

    def test_get_store_container_bucket_stores(self):
        mount_path = "/test-path"
        resource1 = V1ConnectionResource(
            name="ref",
            items=["item1", "item2"],
            is_requested=False,
        )
        store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
            secret=resource1,
        )
        container = self.converter._get_store_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="foo/foo",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            connection=store,
            artifacts=None,
            paths=None,
            mount_path=mount_path,
        )
        assert (
            generate_container_name(INIT_ARTIFACTS_CONTAINER_PREFIX, store.name, False)
            in container.name
        )
        assert container.image == "foo/foo"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["/bin/sh", "-c"]
        assert container.args == [
            get_volume_args(
                store=store,
                mount_path=mount_path,
                artifacts=None,
                paths=None,
            )
        ]
        assert container.env is not None
        assert container.env_from == []
        assert container.resources == get_init_resources()
        assert container.volume_mounts == [
            get_connections_context_mount(
                name=get_volume_name(mount_path), mount_path=mount_path
            )
        ]
