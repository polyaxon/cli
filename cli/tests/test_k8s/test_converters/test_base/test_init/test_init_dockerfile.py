import pytest

from polyaxon._auxiliaries import V1PolyaxonInitContainer, get_init_resources
from polyaxon._containers.names import INIT_DOCKERFILE_CONTAINER_PREFIX
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._contexts import paths as ctx_paths
from polyaxon._flow import V1Plugins
from polyaxon._runner.converter.common import constants
from polyaxon._runner.converter.common.volumes import get_volume_name
from polyaxon._schemas.types.dockerfile import V1DockerfileType
from tests.test_k8s.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestInitDockerfile(BaseConverterTest):
    def test_get_dockerfile_init_container(self):
        dockerfile_args = V1DockerfileType(image="test/test")
        container = self.converter._get_dockerfile_init_container(
            polyaxon_init=V1PolyaxonInitContainer(image="foo", image_tag=""),
            dockerfile_args=dockerfile_args,
            env=None,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path="test",
            run_instance="foo.bar.runs.uuid",
        )
        assert INIT_DOCKERFILE_CONTAINER_PREFIX in container.name
        assert container.image == "foo"
        assert container.image_pull_policy is None
        assert container.command == ["polyaxon", "docker", "generate"]
        assert container.args == [
            "--build-context={}".format(dockerfile_args.to_json()),
            "--destination={}".format(ctx_paths.CONTEXT_MOUNT_ARTIFACTS),
            "--copy-path={}".format(
                ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format("test")
            ),
            "--track",
        ]
        assert container.env == [
            self.converter._get_run_instance_env_var(run_instance="foo.bar.runs.uuid")
        ]
        assert container.resources == get_init_resources()
        assert container.volume_mounts == [
            self.converter._get_connections_context_mount(
                name=constants.VOLUME_MOUNT_ARTIFACTS,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
                run_path=self.converter.run_path,
            ),
            self.converter._get_auth_context_mount(
                read_only=True, run_path=self.converter.run_path
            ),
        ]

        dockerfile_args = V1DockerfileType(
            image="test/test",
            lang_env="LANG",
            run=["step1", "step2"],
            env=[["key1", "val1"], ["key2", "val2"]],
            uid=2222,
            gid=2222,
        )
        container = self.converter._get_dockerfile_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init/init",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            env=[],
            dockerfile_args=dockerfile_args,
            mount_path="/somepath",
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path="test",
            run_instance="foo.bar.runs.uuid",
        )
        assert INIT_DOCKERFILE_CONTAINER_PREFIX in container.name
        assert container.image == "init/init"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["polyaxon", "docker", "generate"]
        assert container.args == [
            "--build-context={}".format(dockerfile_args.to_json()),
            "--destination=/somepath",
            "--copy-path={}".format(
                ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format("test")
            ),
            "--track",
        ]
        assert container.env == [
            self.converter._get_run_instance_env_var(run_instance="foo.bar.runs.uuid")
        ]
        assert container.resources == get_init_resources()
        assert container.volume_mounts == [
            self.converter._get_connections_context_mount(
                name=get_volume_name("/somepath"),
                mount_path="/somepath",
                run_path=self.converter.run_path,
            ),
            self.converter._get_auth_context_mount(
                read_only=True, run_path=self.converter.run_path
            ),
        ]
