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
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.common.volumes import (
    get_artifacts_context_volume,
    get_configs_context_volume,
    get_connections_context_volume,
    get_docker_context_volume,
    get_shm_context_volume,
    get_volume,
    get_volume_from_config_map,
    get_volume_from_connection,
    get_volume_from_secret,
)
from polyaxon._runner.converter.common import constants
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
class TestVolumes(BaseTestCase):
    def test_get_volume_from_connection(self):
        # No store
        assert get_volume_from_connection(connection=None) is None

        # Bucket store
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
        )
        assert get_volume_from_connection(connection=store) is None

        # Claim store
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )
        volume = get_volume_from_connection(connection=store)
        assert volume.name == store.name
        assert volume.persistent_volume_claim.claim_name == store.schema_.volume_claim
        assert volume.persistent_volume_claim.read_only == store.schema_.read_only

        # Host path
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(
                mount_path="/tmp", host_path="/tmp", read_only=True
            ),
        )
        volume = get_volume_from_connection(connection=store)
        assert volume.name == store.name
        assert volume.host_path == k8s_schemas.V1HostPathVolumeSource(
            path=store.schema_.host_path
        )

    def test_get_volume_from_secret(self):
        # No store
        assert get_volume_from_secret(None) is None

        # Store with mount path
        resource1 = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            is_requested=False,
        )
        assert get_volume_from_secret(resource1) is None

        # Claim store
        resource1 = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            mount_path="/tmp",
            is_requested=False,
        )
        volume = get_volume_from_secret(resource1)
        assert volume.name == resource1.name
        assert volume.secret.secret_name == resource1.name
        assert volume.secret.items == resource1.items

    def test_get_volume_from_config_map(self):
        # No store
        assert get_volume_from_config_map(None) is None

        # Store with mount path
        resource1 = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            is_requested=False,
        )
        assert get_volume_from_config_map(resource1) is None

        # Claim store
        resource1 = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            mount_path="/tmp",
            is_requested=False,
        )
        volume = get_volume_from_config_map(resource1)
        assert volume.name == resource1.name
        assert volume.config_map.name == resource1.name
        assert volume.config_map.items == resource1.items

    def test_get_volume(self):
        # Empty dir
        volume = get_volume(volume="test")
        assert volume.name == "test"
        assert isinstance(volume.empty_dir, k8s_schemas.V1EmptyDirVolumeSource)

        # Claim
        volume = get_volume(volume="test", claim_name="claim_name", read_only=True)
        assert volume.name == "test"
        assert volume.persistent_volume_claim.claim_name == "claim_name"
        assert volume.persistent_volume_claim.read_only is True

        # Host path
        volume = get_volume(volume="test", host_path="/tmp", read_only=True)
        assert volume.name == "test"
        assert volume.host_path.path == "/tmp"

    def test_get_docker_context_volume(self):
        volume = get_docker_context_volume()
        assert volume.name == constants.VOLUME_MOUNT_DOCKER
        assert volume.host_path.path == ctx_paths.CONTEXT_MOUNT_DOCKER

    def test_get_configs_context_volume(self):
        volume = get_configs_context_volume()
        assert volume.name == constants.VOLUME_MOUNT_CONFIGS
        assert isinstance(volume.empty_dir, k8s_schemas.V1EmptyDirVolumeSource)

    def test_get_artifacts_context_volume(self):
        volume = get_artifacts_context_volume()
        assert volume.name == constants.VOLUME_MOUNT_ARTIFACTS
        assert isinstance(volume.empty_dir, k8s_schemas.V1EmptyDirVolumeSource)

    def test_get_connections_context_volume(self):
        volume = get_connections_context_volume("foo")
        assert volume.name == "foo"
        assert isinstance(volume.empty_dir, k8s_schemas.V1EmptyDirVolumeSource)

    def test_get_shm_context_volume(self):
        volume = get_shm_context_volume()
        assert volume.name == constants.VOLUME_MOUNT_SHM
        assert isinstance(volume.empty_dir, k8s_schemas.V1EmptyDirVolumeSource)
