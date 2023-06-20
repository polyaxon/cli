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
from polyaxon.docker import docker_types
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.k8s import k8s_schemas
from polyaxon.runner.converter.common import constants
from polyaxon.runner.converter.common.volumes import get_volume_name
from polyaxon.runner.converter.init.store import get_volume_args
from tests.test_docker.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestInitStore(BaseConverterTest):
    def test_get_base_store_container_with_none_values(self):
        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_base_store_container(
                container=docker_types.V1Container(name="init"),
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
            container=docker_types.V1Container(name="test"),
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
        assert container.command == ["/bin/sh", "-c"]
        assert container.args is None
        assert (
            self.converter._get_connection_env_var(
                connection=bucket_store_without_secret
            )
            == []
        )
        assert container.env == [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_store_without_secret]
            )
        ]
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
            container=docker_types.V1Container(name="init"),
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
        assert container.command == ["/bin/sh", "-c"]
        assert container.args is None

        assert (
            self.converter._get_connection_env_var(connection=bucket_store_with_secret)
            == []
        )
        assert container.env == self.converter._get_items_from_json_resource(
            resource=non_mount_resource1
        ) + [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_store_with_secret]
            )
        ]
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
            container=docker_types.V1Container(name="init"),
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
        assert container.command == ["/bin/sh", "-c"]
        assert container.args is None
        assert (
            self.converter._get_connection_env_var(connection=bucket_store_with_secret)
            == []
        )
        assert container.env == [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_store_with_secret]
            )
        ]
        assert container.resources is not None
        assert container.volume_mounts == [
            self.converter._get_mount_from_resource(resource=mount_resource1)
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
            container=docker_types.V1Container(name="init"),
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
        assert container.command == ["/bin/sh", "-c"]
        assert container.args is None
        assert self.converter._get_connection_env_var(connection=claim_store) == []
        assert container.env == [
            self.converter._get_connections_catalog_env_var(connections=[claim_store])
        ]
        assert container.resources is not None
        assert container.volume_mounts == [
            self.converter._get_mount_from_store(store=claim_store)
        ]

    def test_get_base_container(self):
        store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )
        env = [self.converter._get_env_var(name="key", value="value")]
        env_from = [k8s_schemas.V1EnvFromSource(secret_ref={"name": "ref"})]
        mounts = [docker_types.V1VolumeMount(__root__=("-v", "/test"))]
        container = self.converter._get_base_store_container(
            container=docker_types.V1Container(name="init"),
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
        assert container.command == ["/bin/sh", "-c"]
        assert container.args == ["test"]
        assert container.env == env
        assert container.resources is not None
        assert container.volume_mounts == mounts + [
            self.converter._get_mount_from_store(store=store)
        ]

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
            run_path=self.converter.run_path,
        )
        mount_path = ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(store.name)
        assert (
            generate_container_name(INIT_ARTIFACTS_CONTAINER_PREFIX, store.name, False)
            in container.name
        )
        assert container.image == "foo/foo:foo"
        assert container.command == ["/bin/sh", "-c"]
        assert container.args == [
            get_volume_args(
                store=store, mount_path=mount_path, artifacts=None, paths=None
            )
        ]
        assert self.converter._get_connection_env_var(connection=store) == []
        assert container.env == [
            self.converter._get_connections_catalog_env_var(connections=[store])
        ]
        assert container.resources is not None
        assert container.volume_mounts == [
            self.converter._get_connections_context_mount(
                name=constants.VOLUME_MOUNT_ARTIFACTS,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
                run_path=self.converter.run_path,
            ),
            self.converter._get_mount_from_store(store=store),
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
            run_path=self.converter.run_path,
            mount_path=mount_path,
        )
        assert (
            generate_container_name(INIT_ARTIFACTS_CONTAINER_PREFIX, store.name, False)
            in container.name
        )
        assert container.image == "foo/foo"
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
        assert container.resources.to_dict() == {"cpus": "1", "memory": "500Mi"}
        assert container.volume_mounts == [
            self.converter._get_connections_context_mount(
                name=get_volume_name(mount_path),
                mount_path=mount_path,
                run_path=self.converter.run_path,
            )
        ]
