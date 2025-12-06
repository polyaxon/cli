from polyaxon._auxiliaries import V1PolyaxonSidecarContainer
from polyaxon._connections import (
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
)
from polyaxon._flow import V1Plugins
from polyaxon._k8s import k8s_schemas
from tests.test_k8s.test_converters.base import BaseConverterTest


class TestSidecarConnections(BaseConverterTest):
    def test_get_sidecars_with_connections(self):
        store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/claim/path", volume_claim="claim", read_only=True
            ),
        )
        plugins = V1Plugins.get_or_create(
            V1Plugins(
                collect_logs=False,
                collect_artifacts=False,
                auth=True,
                sidecar=V1PolyaxonSidecarContainer(no_connections=False),
            )
        )
        sidecar = k8s_schemas.V1Container(name="sidecar", image="foo")

        containers = self.converter.get_sidecar_containers(
            plugins=plugins,
            artifacts_store=None,
            sidecar_containers=[sidecar],
            polyaxon_sidecar=V1PolyaxonSidecarContainer(image="sidecar/sidecar"),
            connections=[store.name],
            connection_by_names={store.name: store},
        )

        # Check that sidecar has volume mounts
        # Since collect_artifacts=False and collect_logs=False, polyaxon sidecar is not created
        # Only user sidecar is returned
        assert len(containers) == 1
        user_sidecar = containers[0]
        assert "sidecar" in user_sidecar.name

        # Check mounts
        mount_paths = [m.mount_path for m in user_sidecar.volume_mounts]
        assert "/claim/path" in mount_paths

        # Check auth context (since plugins.auth=True)
        # Auth context mount path is /plx-context/configs
        from polyaxon._contexts import paths as ctx_paths

        assert ctx_paths.CONTEXT_MOUNT_CONFIGS in mount_paths

    def test_get_sidecars_with_multiple_connections(self):
        """Test that sidecars get volume mounts for multiple connections."""
        store1 = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/claim/path", volume_claim="claim", read_only=True
            ),
        )
        store2 = V1Connection(
            name="test_claim2",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/claim/path2", volume_claim="claim2", read_only=False
            ),
        )
        plugins = V1Plugins.get_or_create(
            V1Plugins(collect_logs=False, collect_artifacts=False, auth=False)
        )
        sidecar = k8s_schemas.V1Container(name="sidecar", image="foo")

        containers = self.converter.get_sidecar_containers(
            plugins=plugins,
            artifacts_store=None,
            sidecar_containers=[sidecar],
            polyaxon_sidecar=V1PolyaxonSidecarContainer(image="sidecar/sidecar"),
            connections=[store1.name, store2.name],
            connection_by_names={store1.name: store1, store2.name: store2},
        )

        assert len(containers) == 1
        user_sidecar = containers[0]

        # Check both connections are mounted
        mount_paths = [m.mount_path for m in user_sidecar.volume_mounts]
        assert "/claim/path" in mount_paths
        assert "/claim/path2" in mount_paths

    def test_get_sidecars_without_mirroring(self):
        """Test that sidecars do NOT get volume mounts when mirror_connections is False or default."""
        store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/claim/path", volume_claim="claim", read_only=True
            ),
        )
        # plugins without sidecar config (defaults to mirror_connections=None/False)
        plugins = V1Plugins.get_or_create(
            V1Plugins(
                collect_logs=False,
                collect_artifacts=False,
                auth=True,
                sidecar=V1PolyaxonSidecarContainer(no_connections=True),
            )
        )
        sidecar = k8s_schemas.V1Container(name="sidecar", image="foo")

        containers = self.converter.get_sidecar_containers(
            plugins=plugins,
            artifacts_store=None,
            sidecar_containers=[sidecar],
            polyaxon_sidecar=V1PolyaxonSidecarContainer(image="sidecar/sidecar"),
            connections=[store.name],
            connection_by_names={store.name: store},
        )

        assert len(containers) == 1
        user_sidecar = containers[0]

        # Check NO connection mounts are present
        mount_paths = (
            [m.mount_path for m in user_sidecar.volume_mounts]
            if user_sidecar.volume_mounts
            else []
        )
        assert "/claim/path" not in mount_paths
