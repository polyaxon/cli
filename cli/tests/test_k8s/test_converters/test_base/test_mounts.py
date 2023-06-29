import pytest

from polyaxon.connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1ConnectionResource,
    V1HostPathConnection,
)
from polyaxon.contexts import paths as ctx_paths
from polyaxon.k8s.converter.base.mounts import MountsMixin
from polyaxon.runner.converter.common import constants
from tests.test_k8s.test_converters.base import BaseConverterTest


@pytest.mark.k8s_mark
class TestMounts(BaseConverterTest):
    def test_get_mount_from_store(self):
        # Bucket stores
        assert MountsMixin._get_mount_from_store(store=None) is None
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.S3,
            schema_=dict(bucket="s3//:foo"),
        )
        assert MountsMixin._get_mount_from_store(store=store) is None

        assert MountsMixin._get_mount_from_store(store=None) is None
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
        )
        assert MountsMixin._get_mount_from_store(store=store) is None

        # Claim store
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=dict(mount_path="/tmp", volume_claim="test", read_only=True),
        )
        mount = MountsMixin._get_mount_from_store(store=store)
        assert mount.name == store.name
        assert mount.mount_path == store.schema_.mount_path
        assert mount.read_only == store.schema_.read_only

        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )
        mount = MountsMixin._get_mount_from_store(store=store)
        assert mount.name == store.name
        assert mount.mount_path == store.schema_.mount_path
        assert mount.read_only == store.schema_.read_only

        # Host path
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=dict(mount_path="/tmp", host_path="/tmp", read_only=True),
        )
        mount = MountsMixin._get_mount_from_store(store=store)
        assert mount.name == store.name
        assert mount.mount_path == store.schema_.mount_path
        assert mount.read_only == store.schema_.read_only

        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(
                mount_path="/tmp", host_path="/tmp", read_only=True
            ),
        )
        mount = MountsMixin._get_mount_from_store(store=store)
        assert mount.name == store.name
        assert mount.mount_path == store.schema_.mount_path
        assert mount.read_only == store.schema_.read_only

    def test_mount_resources(self):
        # Non mouth resource
        assert MountsMixin._get_mount_from_resource(None) is None
        resource = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            is_requested=False,
        )
        assert MountsMixin._get_mount_from_resource(resource=resource) is None

        assert MountsMixin._get_mount_from_resource(None) is None
        resource = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            is_requested=False,
        )
        assert MountsMixin._get_mount_from_resource(resource=resource) is None

        # Resource with mount
        resource = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            mount_path="/tmp",
            is_requested=False,
        )
        mount = MountsMixin._get_mount_from_resource(resource=resource)
        assert mount.name == resource.name
        assert mount.mount_path == resource.mount_path
        assert mount.read_only is True

        resource = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            mount_path="/tmp",
            is_requested=False,
        )
        mount = MountsMixin._get_mount_from_resource(resource=resource)
        assert mount.name == resource.name
        assert mount.mount_path == resource.mount_path
        assert mount.read_only is True

    def test_get_docker_context_mount(self):
        mount = MountsMixin._get_docker_context_mount()
        assert mount.name == constants.VOLUME_MOUNT_DOCKER
        assert mount.mount_path == ctx_paths.CONTEXT_MOUNT_DOCKER

    def test_get_auth_context_mount(self):
        mount = MountsMixin._get_auth_context_mount(run_path=self.converter.run_path)
        assert mount.name == constants.VOLUME_MOUNT_CONFIGS
        assert mount.mount_path == ctx_paths.CONTEXT_MOUNT_CONFIGS
        assert mount.read_only is None
        mount = MountsMixin._get_auth_context_mount(
            read_only=True,
            run_path=self.converter.run_path,
        )
        assert mount.read_only is True

    def test_get_artifacts_context_mount(self):
        mount = MountsMixin._get_artifacts_context_mount()
        assert mount.name == constants.VOLUME_MOUNT_ARTIFACTS
        assert mount.mount_path == ctx_paths.CONTEXT_MOUNT_ARTIFACTS
        assert mount.read_only is None
        mount = MountsMixin._get_artifacts_context_mount(read_only=True)
        assert mount.read_only is True

    def test_get_connections_context_mount(self):
        mount = MountsMixin._get_connections_context_mount(
            name="test",
            mount_path="/test",
            run_path=self.converter.run_path,
        )
        assert mount.name == "test"
        assert mount.mount_path == "/test"
        assert mount.read_only is None

    def test_get_shm_context_mount(self):
        mount = MountsMixin._get_shm_context_mount()
        assert mount.name == constants.VOLUME_MOUNT_SHM
        assert mount.mount_path == ctx_paths.CONTEXT_MOUNT_SHM
        assert mount.read_only is None

    def test_get_mounts(self):
        assert (
            MountsMixin._get_mounts(
                use_auth_context=False,
                use_artifacts_context=False,
                use_docker_context=False,
                use_shm_context=False,
            )
            == []
        )
        assert MountsMixin._get_mounts(
            use_auth_context=True,
            use_artifacts_context=True,
            use_docker_context=True,
            use_shm_context=True,
        ) == [
            MountsMixin._get_auth_context_mount(
                read_only=True,
                run_path=self.converter.run_path,
            ),
            MountsMixin._get_artifacts_context_mount(read_only=False),
            MountsMixin._get_docker_context_mount(),
            MountsMixin._get_shm_context_mount(),
        ]
