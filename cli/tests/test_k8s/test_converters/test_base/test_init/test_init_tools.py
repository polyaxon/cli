import pytest

from polyaxon._auxiliaries.init import V1PolyaxonInitContainer, get_init_resources
from polyaxon._containers.names import INIT_TOOLS_CONTAINER
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._contexts import paths as ctx_paths
from polyaxon._flow import V1Plugins
from polyaxon._runner.converter.common import constants
from polyaxon.exceptions import PolyaxonConverterError
from tests.test_k8s.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestInitTools(BaseConverterTest):
    def test_get_tools_init_container(self):
        container = self.converter._get_tools_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="foo/foo",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            use_tmux=True,
        )

        assert container.name == INIT_TOOLS_CONTAINER
        assert container.image == "foo/foo"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == [
            "cp",
            "/usr/bin/tmux",
            "/opt/polyaxon/bin/tmux",
        ]
        assert container.args is None
        assert container.resources == get_init_resources()
        assert container.volume_mounts == [
            self.converter._get_tools_bin_context_mount(read_only=False)
        ]

    def test_get_tools_init_container_with_sandbox(self):
        container = self.converter._get_tools_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="foo/foo",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            use_tmux=False,
            use_sandbox=True,
        )

        assert container.command == [
            "sh",
            "-c",
            "cp /usr/bin/plx-exec /opt/polyaxon/bin/plx-exec && "
            "cp /usr/bin/bootstrap-sandbox.sh "
            "/opt/polyaxon/bin/bootstrap-sandbox.sh",
        ]

    def test_get_tools_init_container_with_tmux_and_sandbox(self):
        container = self.converter._get_tools_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="foo/foo",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            use_tmux=True,
            use_sandbox=True,
        )

        assert container.command == [
            "sh",
            "-c",
            "cp /usr/bin/tmux /opt/polyaxon/bin/tmux && "
            "cp /usr/bin/plx-exec /opt/polyaxon/bin/plx-exec && "
            "cp /usr/bin/bootstrap-sandbox.sh "
            "/opt/polyaxon/bin/bootstrap-sandbox.sh",
        ]

    def test_get_tools_init_container_requires_tool(self):
        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_tools_init_container(
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo", image_tag=""),
                use_tmux=False,
                use_sandbox=False,
            )

    def test_get_init_containers_with_sandbox(self):
        containers = self.converter.get_init_containers(
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo", image_tag=""),
            plugins=V1Plugins(sandbox=True),
            artifacts_store=None,
            init_connections=[],
            init_containers=[],
            connection_by_names={},
        )

        assert len(containers) == 1
        assert containers[0].name == INIT_TOOLS_CONTAINER
        assert "/usr/bin/plx-exec" in containers[0].command[-1]

    def test_get_tools_init_container_with_custom_image(self):
        container = self.converter._get_tools_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="custom/init",
                image_tag="v1.0",
                image_pull_policy=PullPolicy.ALWAYS,
            ),
            use_tmux=True,
        )

        assert container.name == INIT_TOOLS_CONTAINER
        assert container.image == "custom/init:v1.0"
        assert container.image_pull_policy == "Always"

    def test_get_tools_init_container_volume_mount(self):
        container = self.converter._get_tools_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="foo/foo",
                image_tag="",
            ),
            use_tmux=True,
        )

        assert len(container.volume_mounts) == 1
        mount = container.volume_mounts[0]
        assert mount.name == constants.VOLUME_MOUNT_TOOLS_BIN
        assert mount.mount_path == ctx_paths.CONTEXT_MOUNT_TOOLS_BIN
        assert mount.read_only is False
