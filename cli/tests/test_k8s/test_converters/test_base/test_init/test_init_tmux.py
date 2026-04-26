import pytest

from polyaxon._auxiliaries.tmux import V1PolyaxonTmuxContainer, get_tmux_resources
from polyaxon._containers.names import INIT_TMUX_CONTAINER
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._contexts import paths as ctx_paths
from polyaxon._runner.converter.common import constants
from tests.test_k8s.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestInitTmux(BaseConverterTest):
    def test_get_tmux_init_container(self):
        container = self.converter._get_tmux_init_container(
            polyaxon_tmux=V1PolyaxonTmuxContainer(
                image="foo/foo",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
        )

        assert container.name == INIT_TMUX_CONTAINER
        assert container.image == "foo/foo"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == [
            "cp",
            "/usr/bin/tmux",
            "/opt/polyaxon/bin/tmux",
        ]
        assert container.args is None
        assert container.resources == get_tmux_resources()
        assert container.volume_mounts == [
            self.converter._get_tmux_bin_context_mount(read_only=False)
        ]

    def test_get_tmux_init_container_with_custom_image(self):
        container = self.converter._get_tmux_init_container(
            polyaxon_tmux=V1PolyaxonTmuxContainer(
                image="custom/tmux",
                image_tag="v1.0",
                image_pull_policy=PullPolicy.ALWAYS,
            ),
        )

        assert container.name == INIT_TMUX_CONTAINER
        assert container.image == "custom/tmux:v1.0"
        assert container.image_pull_policy == "Always"

    def test_get_tmux_init_container_volume_mount(self):
        container = self.converter._get_tmux_init_container(
            polyaxon_tmux=V1PolyaxonTmuxContainer(
                image="foo/foo",
                image_tag="",
            ),
        )

        assert len(container.volume_mounts) == 1
        mount = container.volume_mounts[0]
        assert mount.name == constants.VOLUME_MOUNT_TMUX_BIN
        assert mount.mount_path == ctx_paths.CONTEXT_MOUNT_TMUX_BIN
        assert mount.read_only is False
