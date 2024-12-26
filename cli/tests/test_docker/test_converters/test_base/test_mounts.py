import pytest

from polyaxon._connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1ConnectionResource,
    V1HostPathConnection,
)
from polyaxon._contexts import paths as ctx_paths
from polyaxon._docker import docker_types
from polyaxon._docker.converter.base.mounts import MountsMixin
from tests.test_docker.test_converters.base import BaseConverterTest


@pytest.mark.docker_mark
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
        assert mount == docker_types.V1VolumeMount.make(("-v", "test:/tmp:ro"))

        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )
        mount = MountsMixin._get_mount_from_store(store=store)
        assert mount == docker_types.V1VolumeMount.make(("-v", "test:/tmp:ro"))

        # Host path
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=dict(mount_path="/tmp", host_path="/tmp", read_only=True),
        )
        mount = MountsMixin._get_mount_from_store(store=store)
        assert mount == docker_types.V1VolumeMount.make(("-v", "/tmp:/tmp:ro"))

        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(
                mount_path="/tmp", host_path="/tmp", read_only=True
            ),
        )
        mount = MountsMixin._get_mount_from_store(store=store)
        assert mount == docker_types.V1VolumeMount.make(("-v", "/tmp:/tmp:ro"))

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
            host_path="/tmp",
            is_requested=False,
        )
        mount = MountsMixin._get_mount_from_resource(resource=resource)
        assert mount == docker_types.V1VolumeMount.make(("-v", "/tmp:/tmp:ro"))

        resource = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            mount_path="/tmp",
            host_path="/tmp",
            is_requested=False,
        )
        mount = MountsMixin._get_mount_from_resource(resource=resource)
        assert mount == docker_types.V1VolumeMount.make(("-v", "/tmp:/tmp:ro"))

    def test_get_docker_context_mount(self):
        mount = MountsMixin._get_docker_context_mount()
        assert mount == docker_types.V1VolumeMount.make(
            (
                "-v",
                f"{ctx_paths.CONTEXT_MOUNT_DOCKER}:{ctx_paths.CONTEXT_MOUNT_DOCKER}:ro",
            )
        )

    def test_get_auth_context_mount(self):
        mount = MountsMixin._get_auth_context_mount(run_path="test")
        assert mount.get_root()[0] == "-v"
        assert ".runs/test" in mount.get_root()[1]
        assert ctx_paths.CONTEXT_MOUNT_CONFIGS in mount.get_root()[1]
        assert "ro" not in mount.get_root()[1]
        mount = MountsMixin._get_auth_context_mount(read_only=True, run_path="test")
        assert mount.get_root()[0] == "-v"
        assert ".runs/test" in mount.get_root()[1]
        assert ctx_paths.CONTEXT_MOUNT_CONFIGS in mount.get_root()[1]
        assert "ro" in mount.get_root()[1]

    def test_get_artifacts_context_mount(self):
        mount = MountsMixin._get_artifacts_context_mount()
        assert mount.get_root()[0] == "-v"
        assert ctx_paths.CONTEXT_MOUNT_ARTIFACTS in mount.get_root()[1]
        assert "ro" not in mount.get_root()[1]
        mount = MountsMixin._get_artifacts_context_mount(read_only=True)
        assert mount.get_root()[0] == "-v"
        assert ctx_paths.CONTEXT_MOUNT_ARTIFACTS in mount.get_root()[1]
        assert "ro" in mount.get_root()[1]

    def test_get_connections_context_mount(self):
        mount = MountsMixin._get_connections_context_mount(
            name="test",
            mount_path="/test",
            run_path=self.converter.run_path,
        )
        assert mount == docker_types.V1VolumeMount.make(
            ("-v", "/tmp/plx/.runs/run_uuid:/test")
        )

    def test_get_shm_context_mount(self):
        mount = MountsMixin._get_shm_context_mount()
        assert mount == docker_types.V1VolumeMount.make(
            (
                "--mount",
                f"type=tmpfs,destination={ctx_paths.CONTEXT_MOUNT_SHM}",
            )
        )

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
            run_path="test",
        ) == [
            MountsMixin._get_auth_context_mount(
                read_only=True,
                run_path="test",
            ),
            MountsMixin._get_artifacts_context_mount(
                read_only=False,
                run_path="test",
            ),
            MountsMixin._get_docker_context_mount(),
            MountsMixin._get_shm_context_mount(),
        ]
