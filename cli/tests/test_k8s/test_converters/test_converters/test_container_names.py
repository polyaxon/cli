import re
from unittest.mock import patch
from uuid import UUID

from polyaxon._auxiliaries import V1PolyaxonInitContainer
from polyaxon._connections import (
    CONNECTION_CONFIG,
    V1BucketConnection,
    V1Connection,
    V1ConnectionKind,
    V1GitConnection,
)
from polyaxon._docker.converter.converters.job import JobConverter as DockerJobConverter
from polyaxon._flow.init import V1Init
from polyaxon._flow.operations.compiled_operation import V1CompiledOperation
from polyaxon._flow.plugins import V1Plugins
from polyaxon._flow.run.job import V1Job
from polyaxon._flow.run.service import V1Service
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.converters.job import JobConverter
from polyaxon._k8s.converter.converters.service import ServiceConverter
from polyaxon._local_process.converter.converters.job import (
    JobConverter as LocalProcessJobConverter,
)
from polyaxon._schemas.types import V1TensorboardType
from tests.test_k8s.test_converters.base import BaseConverterTest


class TestGeneratedContainerNames(BaseConverterTest):
    def test_names_in_job_and_tensorboard_service_resources(self):
        for converter_type, run_type, spec_key in (
            (JobConverter, V1Job, "batchJobSpec"),
            (ServiceConverter, V1Service, "serviceSpec"),
        ):
            with self.subTest(converter=converter_type.__name__):
                store = V1Connection(
                    name="Artifact_Store." + "x" * 80,
                    kind=V1ConnectionKind.S3,
                    schema_=V1BucketConnection(bucket="s3://artifacts"),
                )
                git = V1Connection(
                    name="Git_Repository." + "x" * 80,
                    kind=V1ConnectionKind.GIT,
                    schema_=V1GitConnection(url="https://example.com/repo.git"),
                )
                custom = V1Connection(
                    name="Custom_Connection." + "x" * 80,
                    kind=V1ConnectionKind.CUSTOM,
                    schema_={"key": "value"},
                )
                connections = {c.name: c for c in (store, git, custom)}
                converter = converter_type(
                    owner_name="owner-name",
                    project_name="project-name",
                    run_name="run-name",
                    run_uuid="run_uuid",
                    polyaxon_init=V1PolyaxonInitContainer(image="foo/init"),
                )
                operation = V1CompiledOperation(
                    plugins=V1Plugins(
                        auth=False,
                        docker=False,
                        shm=False,
                        tmux=False,
                        collect_artifacts=False,
                        collect_logs=False,
                        collect_resources=False,
                        mount_artifacts_store=False,
                    ),
                    run=run_type(
                        container=k8s_schemas.V1Container(
                            name="main", image="foo/main", command=["tensorboard"]
                        ),
                        init=[
                            V1Init(
                                connection=store.name, paths=["first"], path="/data"
                            ),
                            V1Init(
                                connection=store.name, paths=["second"], path="/data"
                            ),
                            V1Init(connection=git.name, path="/repos"),
                            V1Init(
                                connection=custom.name,
                                path="/custom",
                                container=k8s_schemas.V1Container(
                                    image="foo/custom",
                                    command=["echo"],
                                    args=[custom.name],
                                ),
                            ),
                            V1Init(tensorboard=V1TensorboardType(port=6006)),
                        ],
                    ),
                )
                suffixes = ["012345678" + c for c in "abcde"]
                with patch(
                    "uuid.uuid4",
                    side_effect=[UUID(s + "0" * 22) for s in suffixes],
                ):
                    resource = converter.get_resource(
                        compiled_operation=operation,
                        artifacts_store=store,
                        connection_by_names=connections,
                        secrets=[],
                        config_maps=[],
                    )

                containers = resource[spec_key]["template"].spec.init_containers
                names = [c.name for c in containers]
                assert len(names) == len(set(names)) == 5
                assert [name.rsplit("-", 1)[1] for name in names] == suffixes
                assert names[0][:-11] == names[1][:-11]
                for name in names:
                    assert len(name) <= 63
                    assert re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", name)
                assert all(len(name) == 63 for name in names[:4])
                for container, connection in zip(
                    containers, (store, store, git, custom)
                ):
                    catalog = next(
                        e.value
                        for e in container.env
                        if e.name
                        == CONNECTION_CONFIG.get_connections_catalog_env_name()
                    )
                    assert connection.name in catalog
                    assert connections[connection.name] is connection
                for container, path in zip(containers[:2], ("first", "second")):
                    assert (
                        "--connection-name={}".format(store.name) in container.args[0]
                    )
                    assert "--path-to=/data/{}".format(path) in container.args[0]
                    assert container.volume_mounts[0].mount_path == "/data"
                assert "--repo-path=/repos/{}".format(git.name) in containers[2].args
                assert "--connection={}".format(git.name) in containers[2].args
                assert containers[2].volume_mounts[0].mount_path == "/repos"
                assert containers[3].args == [custom.name]
                assert containers[3].volume_mounts[0].mount_path == "/custom"
                assert containers[4].command == [
                    "polyaxon",
                    "initializer",
                    "tensorboard",
                ]

    def test_docker_and_local_process_names_preserve_git_arguments(self):
        for converter in (DockerJobConverter, LocalProcessJobConverter):
            for connection_name in ("my-repo", "Git_Repository." + "x" * 80):
                with self.subTest(converter=converter, connection=connection_name):
                    connection = V1Connection(
                        name=connection_name,
                        kind=V1ConnectionKind.GIT,
                        schema_=V1GitConnection(url="https://example.com/repo.git"),
                    )
                    with patch("uuid.uuid4", return_value=UUID("a" * 32)):
                        container = converter._get_git_init_container(
                            polyaxon_init=V1PolyaxonInitContainer(image="foo/init"),
                            connection=connection,
                            plugins=None,
                            run_path=self.converter.run_path,
                            mount_path="/repos",
                            track=True,
                        )
                    if connection_name == "my-repo":
                        assert container.name == "polyaxon-init-git-my-repo-aaaaaaaaaa"
                    else:
                        assert len(container.name) == 63
                        assert container.name.endswith("-aaaaaaaaaa")
                        assert re.fullmatch(
                            r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", container.name
                        )
                    assert connection.name == connection_name
                    assert (
                        "--repo-path=/repos/{}".format(connection_name)
                        in container.args
                    )
                    assert "--connection={}".format(connection_name) in container.args
