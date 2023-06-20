import pytest

from polyaxon.connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1ConnectionResource,
    V1HostPathConnection,
)
from polyaxon.containers.pull_policy import PullPolicy
from polyaxon.docker import docker_types
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.polyflow import V1Init, V1Plugins
from polyaxon.services.values import PolyaxonServices
from tests.test_docker.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestMainContainer(BaseConverterTest):
    def setUp(self):
        super().setUp()
        # Secrets and config maps
        self.non_mount_resource1 = V1ConnectionResource(
            name="non_mount_test1",
            items=["item1", "item2"],
            is_requested=False,
        )
        self.request_non_mount_resource1 = V1ConnectionResource(
            name="request_non_mount_resource1",
            items=["item1", "item2"],
            is_requested=True,
        )
        self.non_mount_resource2 = V1ConnectionResource(
            name="non_mount_test2",
            is_requested=False,
        )
        self.mount_resource1 = V1ConnectionResource(
            name="mount_test1",
            items=["item1", "item2"],
            mount_path="/tmp1",
            is_requested=False,
        )
        self.request_mount_resource2 = V1ConnectionResource(
            name="mount_test1",
            mount_path="/tmp2",
            is_requested=True,
        )
        # Connections
        self.gcs_store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
            secret=self.mount_resource1,
        )
        self.s3_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
            secret=self.non_mount_resource1,
        )
        self.az_store = V1Connection(
            name="test_az",
            kind=V1ConnectionKind.WASB,
            schema_=V1BucketConnection(bucket="wasb://x@y.blob.core.windows.net"),
            secret=self.non_mount_resource1,
        )
        self.claim_store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )
        self.host_path_store = V1Connection(
            name="test_path",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(mount_path="/tmp", host_path="/tmp"),
        )

    def assert_artifacts_store_raises(self, store, run_path):
        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_main_container(
                container_id="test",
                main_container=None,
                plugins=V1Plugins(collect_artifacts=True, collect_logs=False),
                artifacts_store=store,
                init=None,
                connection_by_names=None,
                connections=None,
                secrets=None,
                config_maps=None,
                kv_env_vars=None,
                ports=None,
                run_path=run_path,
            )

    def test_get_main_container_with_artifacts_store_with_wrong_paths_raises(self):
        artifacts_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
        )
        self.assert_artifacts_store_raises(store=artifacts_store, run_path=None)

        artifacts_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
        )
        self.assert_artifacts_store_raises(store=artifacts_store, run_path=[])

    def test_get_main_container_with_none_values(self):
        container = self.converter._get_main_container(
            container_id="test",
            main_container=docker_types.V1Container(name="main"),
            plugins=None,
            artifacts_store=None,
            init=None,
            connection_by_names=None,
            connections=None,
            secrets=None,
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path=None,
        )

        assert container.name == "test"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        assert (
            container.env
            == self.converter._get_service_env_vars(
                service_header=PolyaxonServices.RUNNER,
                external_host=False,
                log_level=None,
            )
            + self.converter._get_additional_env_vars()
        )
        assert container.resources is None
        assert container.volume_mounts == []

    def test_get_main_container_simple_params(self):
        container = self.converter._get_main_container(
            container_id="new-name",
            main_container=docker_types.V1Container(
                name="main",
                image="job_docker_image",
                command=["cmd", "-p", "-c"],
                args=["arg1", "arg2"],
                resources={"cpus": 1, "memory": "256Mi"},
            ),
            plugins=None,
            artifacts_store=None,
            init=None,
            connection_by_names=None,
            connections=None,
            secrets=None,
            config_maps=None,
            kv_env_vars=None,
            ports=23,
            run_path=None,
        )

        assert container.name == "new-name"
        assert container.image == "job_docker_image"
        assert container.command == ["cmd", "-p", "-c"]
        assert container.args == ["arg1", "arg2"]
        assert container.ports[0].__root__ == "23"
        assert container.resources.to_dict() == {"cpus": "1", "memory": "256Mi"}
        assert container.volume_mounts == []

    def test_get_main_container_with_mounted_artifacts_store(self):
        container = self.converter._get_main_container(
            container_id="test",
            main_container=docker_types.V1Container(name="main"),
            plugins=None,
            artifacts_store=None,
            init=[V1Init(connection=self.claim_store.name)],
            connections=None,
            connection_by_names={self.claim_store.name: self.claim_store},
            secrets=None,
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )
        base_env = (
            self.converter._get_service_env_vars(
                service_header=PolyaxonServices.RUNNER,
                external_host=False,
                log_level=None,
            )
            + self.converter._get_additional_env_vars()
        )

        assert container.name == "test"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        assert container.resources is None
        assert len(container.volume_mounts) == 1

        # Mount store
        container = self.converter._get_main_container(
            container_id="test",
            main_container=docker_types.V1Container(name="main"),
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    mount_artifacts_store=True,
                    collect_artifacts=True,
                    collect_logs=True,
                    collect_resources=True,
                    shm=False,
                )
            ),
            artifacts_store=None,
            init=[V1Init(connection=self.claim_store.name)],
            connections=None,
            connection_by_names={self.claim_store.name: self.claim_store},
            secrets=None,
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )

        assert container.name == "test"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        assert container.resources is None
        assert len(container.volume_mounts) == 1  # store not passed

        container = self.converter._get_main_container(
            container_id="",
            main_container=docker_types.V1Container(name="main"),
            plugins=None,
            artifacts_store=None,
            init=[V1Init(connection=self.claim_store.name)],
            connections=[self.claim_store.name],
            connection_by_names={self.claim_store.name: self.claim_store},
            secrets=None,
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )

        assert container.name == "main"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        assert container.resources is None
        assert len(container.volume_mounts) == 2

        container = self.converter._get_main_container(
            container_id="main-job",
            main_container=docker_types.V1Container(name="main"),
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    collect_artifacts=True,
                    collect_logs=True,
                    collect_resources=True,
                    shm=False,
                )
            ),
            artifacts_store=self.claim_store,
            init=None,
            connections=[],
            connection_by_names={self.claim_store.name: self.claim_store},
            secrets=None,
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )

        assert container.name == "main-job"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        # One from the artifacts store name env var + base envs
        assert len(container.env) == 2 + 1 + len(base_env)
        assert container.resources is None
        assert len(container.volume_mounts) == 1

        # Mount store
        container = self.converter._get_main_container(
            container_id="main-job",
            main_container=docker_types.V1Container(name="main"),
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    mount_artifacts_store=True,
                    collect_artifacts=True,
                    collect_logs=True,
                    collect_resources=True,
                    shm=False,
                )
            ),
            artifacts_store=self.claim_store,
            init=None,
            connections=[],
            connection_by_names={self.claim_store.name: self.claim_store},
            secrets=None,
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )

        assert container.name == "main-job"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        # One from the artifacts store name env var and the schema + base envs
        assert len(container.env) == 2 + 1 + 1 + len(base_env)
        assert container.resources is None
        assert len(container.volume_mounts) == 2

    def test_get_main_container_with_bucket_artifacts_store(self):
        container = self.converter._get_main_container(
            container_id="main",
            main_container=docker_types.V1Container(name="main"),
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    collect_artifacts=True,
                    collect_logs=True,
                    collect_resources=True,
                    shm=False,
                )
            ),
            artifacts_store=self.s3_store,
            init=None,
            connections=None,
            connection_by_names={self.s3_store.name: self.s3_store},
            secrets=None,
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )
        base_env = (
            self.converter._get_service_env_vars(
                service_header=PolyaxonServices.RUNNER,
                external_host=False,
                log_level=None,
            )
            + self.converter._get_additional_env_vars()
        )

        assert container.name == "main"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        # One from the secret key items + base envs
        assert len(container.env) == 1 + 2 + len(base_env)
        assert container.resources is None
        assert len(container.volume_mounts) == 1  # mount context

        # Mount store
        container = self.converter._get_main_container(
            container_id="main",
            main_container=docker_types.V1Container(name="main"),
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    mount_artifacts_store=True,
                    collect_artifacts=False,
                    collect_logs=False,
                    collect_resources=False,
                    shm=False,
                )
            ),
            artifacts_store=self.gcs_store,
            init=None,
            connections=None,
            connection_by_names={self.gcs_store.name: self.gcs_store},
            secrets=None,
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )

        assert container.name == "main"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        # the secret key items are mounted + base envs
        assert len(container.env) == 2 + len(base_env)
        assert container.resources is None
        assert len(container.volume_mounts) == 1  # mount resource

        container = self.converter._get_main_container(
            container_id="main1",
            main_container=docker_types.V1Container(name="main"),
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    collect_artifacts=True,
                    collect_logs=True,
                    collect_resources=True,
                    sync_statuses=True,
                    shm=False,
                )
            ),
            artifacts_store=self.s3_store,
            init=None,
            connections=None,
            connection_by_names={self.s3_store.name: self.s3_store},
            secrets=[self.mount_resource1],
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )

        assert container.name == "main1"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        # One from the artifacts store name env var + base envs
        assert len(container.env) == 2 + 1 + len(base_env)
        assert container.resources is None
        # The mount resource1 is not requested
        assert len(container.volume_mounts) == 1  # one mount resource

        container = self.converter._get_main_container(
            container_id="main1",
            main_container=docker_types.V1Container(name="main"),
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    collect_artifacts=True,
                    collect_logs=True,
                    collect_resources=True,
                    shm=False,
                )
            ),
            artifacts_store=self.s3_store,
            init=None,
            connections=None,
            connection_by_names={self.s3_store.name: self.s3_store},
            secrets=[self.request_mount_resource2],
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )

        assert container.name == "main1"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        # One from the artifacts store name env var + base envs
        assert len(container.env) == 2 + 1 + len(base_env)
        assert container.resources is None
        # The mount resource2 is requested
        assert len(container.volume_mounts) == 2  # one mount resource

        container = self.converter._get_main_container(
            container_id="tensorflow",
            main_container=docker_types.V1Container(name="main"),
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    collect_artifacts=True,
                    collect_logs=True,
                    collect_resources=False,
                    shm=False,
                )
            ),
            artifacts_store=self.s3_store,
            init=None,
            connections=None,
            connection_by_names={self.s3_store.name: self.s3_store},
            secrets=[self.non_mount_resource1],
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )

        assert container.name == "tensorflow"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        # One from the artifacts store name env var + base envs
        assert len(container.env) == 1 + 1 + len(base_env)
        assert container.resources is None
        assert len(container.volume_mounts) == 1  # outputs context

        container = self.converter._get_main_container(
            container_id="pytorch",
            main_container=docker_types.V1Container(name="main"),
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    collect_artifacts=True,
                    collect_logs=True,
                    collect_resources=True,
                    shm=False,
                )
            ),
            artifacts_store=self.s3_store,
            init=None,
            connections=None,
            connection_by_names={self.s3_store.name: self.s3_store},
            secrets=[self.request_non_mount_resource1],
            config_maps=None,
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )

        assert container.name == "pytorch"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        # 2 + 2 env vars from the secret mount + 1 from the artifacts store name env var + base envs
        # Normally 2 + 2 + 1 + len(base_env) but the agent secret is not requested
        assert len(container.env) == 2 + 1 + len(base_env)
        assert container.resources is None
        assert len(container.volume_mounts) == 1

    def test_get_main_container(self):
        container = self.converter._get_main_container(
            container_id="test",
            main_container=docker_types.V1Container(name="main"),
            plugins=None,
            artifacts_store=None,
            init=[
                V1Init(connection=self.claim_store.name),
                V1Init(connection=self.s3_store.name),
            ],
            connections=[self.host_path_store.name, self.gcs_store.name],
            connection_by_names={
                self.claim_store.name: self.claim_store,
                self.s3_store.name: self.s3_store,
                self.host_path_store.name: self.host_path_store,
                self.gcs_store.name: self.gcs_store,
            },
            secrets=[self.mount_resource1, self.request_non_mount_resource1],
            config_maps=[self.non_mount_resource1, self.request_mount_resource2],
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )
        base_env = (
            self.converter._get_service_env_vars(
                service_header=PolyaxonServices.RUNNER,
                external_host=False,
                log_level=None,
            )
            + self.converter._get_additional_env_vars()
        )

        assert container.name == "test"
        assert container.image is None
        assert container.command is None
        assert container.args is None
        assert container.ports == []
        # 2 env vars from the secret mount
        # + 1 for the connections catalog
        # + all base env vars
        # Normally 3 + len(base_env) but the agent secret are not exposed
        assert len(container.env) == 1 + len(base_env)
        assert container.resources is None
        assert len(container.volume_mounts) == 4

    def test_get_main_container_host_paths(self):
        plugins = V1Plugins(
            auth=True,
            docker=False,
            shm=False,
            mount_artifacts_store=False,
            collect_logs=True,
            collect_artifacts=True,
            collect_resources=True,
            auto_resume=True,
            sync_statuses=True,
            external_host=False,
            sidecar=None,
        )

        artifacts_store = V1Connection(
            name="plx-outputs",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(
                mount_path="/tmp/plx/outputs", host_path="/tmp/plx/outputs"
            ),
        )

        container = self.converter._get_main_container(
            container_id="test",
            main_container=docker_types.V1Container(name="main"),
            plugins=V1Plugins.get_or_create(plugins),
            artifacts_store=artifacts_store,
            init=[],
            connections=[],
            connection_by_names={artifacts_store.name: artifacts_store},
            secrets=[],
            config_maps=[],
            kv_env_vars=None,
            ports=None,
            run_path="run_path",
        )

        assert container.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(
                read_only=False, run_path="run_path"
            ),
        ]
