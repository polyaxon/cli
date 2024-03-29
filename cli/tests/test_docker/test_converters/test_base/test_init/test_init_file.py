import pytest

from polyaxon._auxiliaries import V1PolyaxonInitContainer
from polyaxon._containers.names import INIT_FILE_CONTAINER_PREFIX
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._contexts import paths as ctx_paths
from polyaxon._flow import V1Plugins
from polyaxon._runner.converter.common import constants
from polyaxon._schemas.types import V1FileType
from tests.test_docker.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestInitFile(BaseConverterTest):
    def test_get_file_init_container(self):
        file_args = V1FileType(content="test")
        container = self.converter._get_file_init_container(
            polyaxon_init=V1PolyaxonInitContainer(image="foo", image_tag=""),
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            file_args=file_args,
            run_path="test",
            run_instance="foo.bar.runs.uuid",
        )
        assert INIT_FILE_CONTAINER_PREFIX in container.name
        assert container.image == "foo"
        assert container.command == ["polyaxon", "initializer", "file"]
        assert container.resources.to_dict() == {"cpus": "1.0", "memory": "0.49G"}
        assert container.volume_mounts == [
            self.converter._get_connections_context_mount(
                name=constants.VOLUME_MOUNT_ARTIFACTS,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
                run_path="test",
            ),
            self.converter._get_auth_context_mount(read_only=True, run_path="test"),
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
        container = self.converter._get_file_init_container(
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
        assert container.command == ["polyaxon", "initializer", "file"]
        assert container.args == [
            "--file-context={}".format(file_args.to_json()),
            "--filepath={}".format(ctx_paths.CONTEXT_MOUNT_ARTIFACTS),
            "--copy-path={}".format(
                ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format("test")
            ),
            "--track",
        ]
        assert container.resources.to_dict() == {"cpus": "1.0", "memory": "0.49G"}
        assert container.volume_mounts == [
            self.converter._get_connections_context_mount(
                name=constants.VOLUME_MOUNT_ARTIFACTS,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
                run_path="test",
            ),
            self.converter._get_auth_context_mount(read_only=True, run_path="test"),
        ]
