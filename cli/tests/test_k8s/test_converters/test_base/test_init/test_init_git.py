import pytest

from polyaxon.auxiliaries import V1PolyaxonInitContainer, get_init_resources
from polyaxon.connections import V1Connection, V1ConnectionKind, V1GitConnection
from polyaxon.containers.names import INIT_GIT_CONTAINER_PREFIX, generate_container_name
from polyaxon.containers.pull_policy import PullPolicy
from polyaxon.contexts import paths as ctx_paths
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.polyflow import V1Plugins
from polyaxon.runner.converter.common import constants
from polyaxon.runner.converter.common.volumes import get_volume_name
from tests.test_k8s.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestInitGit(BaseConverterTest):
    def test_get_git_init_container_raises_for_missing_info(self):
        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_git_init_container(
                polyaxon_init=V1PolyaxonInitContainer(),
                connection=None,
                plugins=None,
                run_path=self.converter.run_path,
            )

        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_git_init_container(
                polyaxon_init=V1PolyaxonInitContainer(image="foo/test"),
                connection=None,
                mount_path=None,
                plugins=None,
                run_path=self.converter.run_path,
            )

    def test_get_git_init_container(self):
        connection = V1Connection(
            name="user/foo",
            kind=V1ConnectionKind.GIT,
            schema_=V1GitConnection(url="foo.com"),
        )
        container = self.converter._get_git_init_container(
            polyaxon_init=V1PolyaxonInitContainer(image="foo", image_tag=""),
            connection=connection,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path=self.converter.run_path,
        )
        assert (
            generate_container_name(INIT_GIT_CONTAINER_PREFIX, connection.name, False)
            in container.name
        )
        assert container.image == "foo"
        assert container.image_pull_policy is None
        assert container.command == ["polyaxon", "initializer", "git"]
        assert self.converter._get_connection_env_var(connection=connection) == []
        assert container.env == [
            self.converter._get_connections_catalog_env_var(connections=[connection])
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

        container = self.converter._get_git_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init/init",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            connection=connection,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path=self.converter.run_path,
        )
        assert (
            generate_container_name(INIT_GIT_CONTAINER_PREFIX, connection.name, False)
            in container.name
        )
        assert container.image == "init/init"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["polyaxon", "initializer", "git"]
        assert container.args == [
            "--repo-path={}/{}".format(
                ctx_paths.CONTEXT_MOUNT_ARTIFACTS, connection.name
            ),
            "--url={}".format(connection.schema_.url),
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

        connection = V1Connection(
            name="user/foo",
            kind=V1ConnectionKind.GIT,
            schema_=V1GitConnection(
                url="foo.com", revision="00b9d2ea01c40f58d6b4051319f9375675a43c02"
            ),
        )
        container = self.converter._get_git_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init/init",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            connection=connection,
            mount_path="/somepath",
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path=self.converter.run_path,
        )
        assert (
            generate_container_name(INIT_GIT_CONTAINER_PREFIX, connection.name, False)
            in container.name
        )
        assert container.image == "init/init"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["polyaxon", "initializer", "git"]
        assert container.args == [
            "--repo-path=/somepath/{}".format(connection.name),
            "--url={}".format(connection.schema_.url),
            "--revision=00b9d2ea01c40f58d6b4051319f9375675a43c02",
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

        connection = V1Connection(
            name="user/foo",
            kind=V1ConnectionKind.GIT,
            schema_=V1GitConnection(
                url="foo.com",
                revision="00b9d2ea01c40f58d6b4051319f9375675a43c02",
                flags=["--falg1", "--flag2=test", "k=v"],
            ),
        )
        container = self.converter._get_git_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init/init",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            connection=connection,
            mount_path="/somepath",
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path=self.converter.run_path,
        )
        assert (
            generate_container_name(INIT_GIT_CONTAINER_PREFIX, connection.name, False)
            in container.name
        )
        assert container.image == "init/init"
        assert container.image_pull_policy == "IfNotPresent"
        assert container.command == ["polyaxon", "initializer", "git"]
        assert container.args == [
            "--repo-path=/somepath/{}".format(connection.name),
            "--url={}".format(connection.schema_.url),
            "--revision=00b9d2ea01c40f58d6b4051319f9375675a43c02",
            '--flags=["--falg1","--flag2=test","k=v"]',
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
