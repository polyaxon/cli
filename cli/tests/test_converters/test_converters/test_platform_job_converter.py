#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import uuid

from polyaxon import settings
from polyaxon.auxiliaries import V1PolyaxonInitContainer, V1PolyaxonSidecarContainer
from polyaxon.connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1K8sResource,
)
from polyaxon.converter.converters.job import PlatformJobConverter
from polyaxon.converter.init.artifacts import get_artifacts_path_container
from polyaxon.converter.init.auth import get_auth_context_container
from polyaxon.converter.init.dockerfile import get_dockerfile_init_container
from polyaxon.converter.init.file import get_file_init_container
from polyaxon.converter.init.git import get_git_init_container
from polyaxon.converter.init.store import get_store_container
from polyaxon.converter.init.tensorboard import get_tensorboard_init_container
from polyaxon.converter.main.container import get_main_container
from polyaxon.converter.sidecar.container import get_sidecar_container
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.mounts import get_mounts
from polyaxon.polyflow import V1Init, V1Plugins
from polyaxon.schemas.types import (
    V1ArtifactsType,
    V1DockerfileType,
    V1FileType,
    V1GitType,
    V1TensorboardType,
)
from polyaxon.services.values import PolyaxonServices
from polyaxon.utils.test_utils import BaseTestCase
from traceml.artifacts import V1ArtifactKind


class DummyConverter(PlatformJobConverter):
    SPEC_KIND = "dumy"
    K8S_ANNOTATIONS_KIND = "dummy-name"
    MAIN_CONTAINER_ID = "dummy"


class TestJobConverter(BaseTestCase):
    SET_AGENT_SETTINGS = True

    def setUp(self):
        super().setUp()
        settings.AGENT_CONFIG.app_secret_name = "polyaxon"
        settings.AGENT_CONFIG.agent_secret_name = "agent"
        settings.CLIENT_CONFIG.host = "https://polyaxon.com"
        self.converter = DummyConverter(
            owner_name="owner-name",
            project_name="project-name",
            run_name="run-name",
            run_uuid="run_uuid",
        )

    def assert_containers(self, results, expected):
        for c in results:
            if "default" not in c.name and "auth" not in c.name:
                c.name = "-".join(c.name.split("-")[:-1])
        for c in expected:
            if "default" not in c.name and "auth" not in c.name:
                c.name = "-".join(c.name.split("-")[:-1])
        assert results == expected

    def test_get_main_env_vars(self):
        env_vars = self.converter.get_main_env_vars()
        assert env_vars == self.converter.get_service_env_vars(
            service_header=PolyaxonServices.RUNNER
        )

    def test_get_init_containers_with_auth(self):
        containers = self.converter.get_init_containers(
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_logs=False, collect_artifacts=False, auth=True)
            ),
            artifacts_store=None,
            init_connections=None,
            connection_by_names={},
            init_containers=[],
        )
        assert containers == [
            get_auth_context_container(
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                env=self.converter.get_auth_service_env_vars(),
            )
        ]

    def test_get_init_containers_none(self):
        containers = self.converter.get_init_containers(
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
            plugins=None,
            artifacts_store=None,
            init_connections=None,
            connection_by_names={},
            init_containers=[],
        )
        assert containers == []

    def test_get_init_containers_with_claim_outputs(self):  # TODO
        store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/claim/path", volume_claim="claim", read_only=True
            ),
        )

        # No context to enable the outputs
        containers = self.converter.get_init_containers(
            plugins=None,
            artifacts_store=store.name,
            init_connections=None,
            connection_by_names={},
            init_containers=[],
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        assert containers == []

        # Enable outputs
        containers = self.converter.get_init_containers(
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_artifacts=True, collect_logs=False)
            ),
            artifacts_store=store,
            connection_by_names={},
            init_connections=None,
            init_containers=[],
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        self.assert_containers(
            containers,
            [
                get_artifacts_path_container(
                    polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                    artifacts_store=store,
                    run_path=self.converter.run_path,
                    auto_resume=True,
                ),
            ],
        )

        # Use store for init
        containers = self.converter.get_init_containers(
            plugins=None,
            artifacts_store=None,
            connection_by_names={store.name: store},
            init_connections=[V1Init(connection=store.name)],
            init_containers=[],
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        self.assert_containers(
            containers,
            [
                get_store_container(
                    polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                    connection=store,
                    artifacts=None,
                    paths=None,
                    env=self.converter.get_init_service_env_vars(),
                )
            ],
        )

        # Use store for init and outputs
        containers = self.converter.get_init_containers(
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_artifacts=True, collect_logs=False)
            ),
            artifacts_store=store,
            init_connections=[V1Init(connection=store.name)],
            connection_by_names={store.name: store},
            init_containers=[],
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        self.assert_containers(
            containers,
            [
                get_artifacts_path_container(
                    polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                    artifacts_store=store,
                    run_path=self.converter.run_path,
                    auto_resume=True,
                ),
                get_store_container(
                    polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                    connection=store,
                    artifacts=None,
                    paths=None,
                    env=self.converter.get_init_service_env_vars(),
                    is_default_artifacts_store=True,
                ),
            ],
        )

        # Add Store
        store1 = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3://foo"),
            secret=None,
        )

        containers = self.converter.get_init_containers(
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_artifacts=True, collect_logs=False, auth=True)
            ),
            artifacts_store=store,
            init_connections=[
                V1Init(
                    connection=store.name,
                    artifacts=V1ArtifactsType(
                        files=["/foo", "/bar", ["from-foo", "to-foo"]]
                    ),
                ),
                V1Init(
                    connection=store1.name,
                    artifacts=V1ArtifactsType(
                        files=["/foo", "/bar", ["from-foo", "to-foo"]]
                    ),
                ),
                V1Init(
                    connection=store1.name,
                    paths=["/foo", "/bar", ["from-foo", "to-foo"]],
                ),
            ],
            connection_by_names={store.name: store, store1.name: store1},
            init_containers=[],
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        self.assert_containers(
            containers,
            [
                get_auth_context_container(
                    polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                    env=self.converter.get_auth_service_env_vars(),
                ),
                get_artifacts_path_container(
                    polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                    artifacts_store=store,
                    run_path=self.converter.run_path,
                    auto_resume=True,
                ),
                get_store_container(
                    polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                    connection=store,
                    artifacts=V1ArtifactsType(
                        files=["/foo", "/bar", ["from-foo", "to-foo"]]
                    ),
                    paths=None,
                    env=self.converter.get_init_service_env_vars(),
                    is_default_artifacts_store=True,
                ),
                get_store_container(
                    polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                    connection=store1,
                    artifacts=V1ArtifactsType(
                        files=["/foo", "/bar", ["from-foo", "to-foo"]]
                    ),
                    paths=None,
                    env=self.converter.get_init_service_env_vars(),
                ),
                get_store_container(
                    polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                    connection=store1,
                    artifacts=None,
                    paths=["/foo", "/bar", ["from-foo", "to-foo"]],
                    env=self.converter.get_init_service_env_vars(),
                ),
            ],
        )

    def test_get_init_containers_with_dockerfiles(self):
        dockerfile_args1 = V1DockerfileType(
            image="foo/test", lang_env="LANG", env=[], run=["step1", "step2"]
        )
        dockerfile_args2 = V1DockerfileType(
            image="foo/test",
            lang_env="LANG",
            env=[],
            run=["step1", "step2"],
            filename="dockerfile2",
            path=["/test"],
        )
        containers = self.converter.get_init_containers(
            plugins=None,
            artifacts_store=None,
            init_connections=[
                V1Init(dockerfile=dockerfile_args1),
                V1Init(dockerfile=dockerfile_args2, path="/test"),
            ],
            init_containers=[],
            connection_by_names={},
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        expected_containers = [
            get_dockerfile_init_container(
                dockerfile_args=dockerfile_args1,
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                env=self.converter.get_init_service_env_vars(),
                plugins=None,
                run_path=self.converter.run_path,
                run_instance=self.converter.run_instance,
            ),
            get_dockerfile_init_container(
                dockerfile_args=dockerfile_args2,
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                env=self.converter.get_init_service_env_vars(),
                mount_path="/test",
                plugins=None,
                run_path=self.converter.run_path,
                run_instance=self.converter.run_instance,
            ),
        ]

        self.assert_containers(expected_containers, containers)

    def test_get_init_containers_with_files(self):
        file_args1 = V1FileType(filename="test.sh", content="test", chmod="+x")
        file_args2 = V1FileType(
            filename="test.csv",
            content="csv",
            kind=V1ArtifactKind.CSV,
        )
        containers = self.converter.get_init_containers(
            plugins=None,
            artifacts_store=None,
            init_connections=[
                V1Init(file=file_args1),
                V1Init(file=file_args2, path="/test"),
            ],
            init_containers=[],
            connection_by_names={},
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        expected_containers = [
            get_file_init_container(
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                file_args=file_args1,
                env=self.converter.get_init_service_env_vars(),
                plugins=None,
                run_path=self.converter.run_path,
                run_instance=self.converter.run_instance,
            ),
            get_file_init_container(
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                file_args=file_args2,
                env=self.converter.get_init_service_env_vars(),
                mount_path="/test",
                plugins=None,
                run_path=self.converter.run_path,
                run_instance=self.converter.run_instance,
            ),
        ]

        self.assert_containers(expected_containers, containers)

    def test_get_init_containers_with_tensorboard(self):
        store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3://foo"),
        )
        uuids = [uuid.uuid4(), uuid.uuid4()]
        tb_args1 = V1TensorboardType(port=8000, uuids=uuids, plugins="plug1,plug2")
        tb_args2 = V1TensorboardType(port=8000, uuids=uuids[0].hex, use_names=True)
        containers = self.converter.get_init_containers(
            plugins=None,
            artifacts_store=store,
            init_connections=[
                V1Init(tensorboard=tb_args1),
                V1Init(tensorboard=tb_args2, path="/test"),
            ],
            init_containers=[],
            connection_by_names={},
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        expected_containers = [
            get_tensorboard_init_container(
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                artifacts_store=store,
                tb_args=tb_args1,
                env=self.converter.get_init_service_env_vars(),
                plugins=None,
                run_instance=self.converter.run_instance,
            ),
            get_tensorboard_init_container(
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                artifacts_store=store,
                tb_args=tb_args2,
                env=self.converter.get_init_service_env_vars(),
                mount_path="/test",
                plugins=None,
                run_instance=self.converter.run_instance,
            ),
        ]

        self.assert_containers(expected_containers, containers)

    def test_get_init_containers_with_git_without_connection(self):
        git1 = V1GitType(revision="test", url="https://test.com")
        git2 = V1GitType(
            revision="test",
            url="https://test.com",
            flags=["--falg1", "--flag2=test", "k=v"],
        )
        containers = self.converter.get_init_containers(
            plugins=None,
            artifacts_store=None,
            init_connections=[
                V1Init(git=git1, container=k8s_schemas.V1Container(name="test")),
                V1Init(git=git2, path="/test"),
            ],
            init_containers=[],
            connection_by_names={},
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        expected_containers = [
            get_git_init_container(
                connection=V1Connection(
                    name=git1.get_name(), kind=V1ConnectionKind.GIT, schema_=git1
                ),
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                env=self.converter.get_init_service_env_vars(),
                plugins=None,
            ),
            get_git_init_container(
                container=k8s_schemas.V1Container(name="test"),
                connection=V1Connection(
                    name=git2.get_name(), kind=V1ConnectionKind.GIT, schema_=git2
                ),
                mount_path="/test",
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                env=self.converter.get_init_service_env_vars(),
                plugins=None,
            ),
        ]
        self.assert_containers(expected_containers, containers)

    def test_get_init_containers_with_store_outputs(self):
        store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3://foo"),
        )

        # No context
        containers = self.converter.get_init_containers(
            plugins=None,
            artifacts_store=store,
            init_connections=[],
            init_containers=[],
            connection_by_names={},
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        assert containers == []

        # With context
        containers = self.converter.get_init_containers(
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_artifacts=True, collect_logs=False, auth=True)
            ),
            artifacts_store=store,
            init_connections=[],
            init_containers=[],
            connection_by_names={},
            polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
        )
        assert containers == [
            get_auth_context_container(
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                env=self.converter.get_auth_service_env_vars(),
            ),
            get_artifacts_path_container(
                polyaxon_init=V1PolyaxonInitContainer(image="foo/foo"),
                artifacts_store=store,
                run_path=self.converter.run_path,
                auto_resume=True,
            ),
        ]

    def test_get_sidecars(self):
        assert (
            self.converter.get_sidecar_containers(
                plugins=None,
                artifacts_store=None,
                sidecar_containers=[],
                polyaxon_sidecar=V1PolyaxonSidecarContainer(
                    image="sidecar/sidecar", sleep_interval=12, sync_interval=-1
                ),
            )
            == []
        )

        # Store with single path, no secret is passed and not required
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3://foo"),
        )
        plugins = V1Plugins.get_or_create(
            V1Plugins(collect_logs=True, collect_artifacts=True, auth=True)
        )
        assert self.converter.get_sidecar_containers(
            plugins=plugins,
            artifacts_store=store,
            sidecar_containers=[],
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar", sleep_interval=12, sync_interval=12
            ),
        ) == [
            get_sidecar_container(
                container_id="dummy",
                plugins=plugins,
                env=self.converter.get_polyaxon_sidecar_service_env_vars(),
                polyaxon_sidecar=V1PolyaxonSidecarContainer(
                    image="sidecar/sidecar", sleep_interval=12, sync_interval=12
                ),
                artifacts_store=store,
                run_path=self.converter.run_path,
            )
        ]

        secret1 = V1K8sResource(
            name="test1",
            items=["item1", "item2"],
            is_requested=True,
        )
        store.secret = secret1

        polyaxon_sidecar = V1PolyaxonSidecarContainer(
            image="sidecar/sidecar",
            image_pull_policy=None,
            sleep_interval=12,
            sync_interval=-1,
        )

        assert self.converter.get_sidecar_containers(
            plugins=plugins,
            artifacts_store=store,
            polyaxon_sidecar=polyaxon_sidecar,
            sidecar_containers=[],
        ) == [
            get_sidecar_container(
                container_id="dummy",
                plugins=plugins,
                env=self.converter.get_polyaxon_sidecar_service_env_vars(),
                polyaxon_sidecar=polyaxon_sidecar,
                artifacts_store=store,
                run_path=self.converter.run_path,
            )
        ]

    def test_main_container(self):
        store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3://foo"),
            secret=None,
        )
        plugins = V1Plugins.get_or_create(V1Plugins(), auth=True)
        main_container = k8s_schemas.V1Container(
            name="main",
            image="foo/test",
            image_pull_policy="IfNotPresent",
            command=["foo", "bar"],
            args=["arg1", "arg2"],
        )
        container = self.converter.get_main_container(
            main_container=main_container,
            plugins=plugins,
            artifacts_store=store,
            init_connections=[],
            connections=[],
            connection_by_names={},
            log_level="info",
            secrets=[],
            config_maps=[],
            kv_env_vars=[],
            ports=None,
        )
        expected_container = get_main_container(
            container_id="dummy",
            main_container=main_container,
            plugins=plugins,
            volume_mounts=get_mounts(
                use_auth_context=True,
                use_artifacts_context=False,
                use_docker_context=False,
                use_shm_context=False,
            ),
            artifacts_store=store,
            connections=[],
            init=[],
            connection_by_names={},
            secrets=[],
            config_maps=[],
            kv_env_vars=[],
            env=self.converter.get_main_env_vars(log_level="info"),
            ports=None,
            run_path="/test",
        )

        assert container == expected_container
