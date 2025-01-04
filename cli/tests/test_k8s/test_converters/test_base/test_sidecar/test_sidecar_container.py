import pytest

from polyaxon._auxiliaries import V1PolyaxonSidecarContainer, get_sidecar_resources
from polyaxon._connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1ConnectionResource,
    V1HostPathConnection,
)
from polyaxon._containers.names import MAIN_JOB_CONTAINER, SIDECAR_CONTAINER
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._flow import V1Plugins
from polyaxon.exceptions import PolyaxonConverterError
from tests.test_k8s.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestSidecarContainer(BaseConverterTest):
    def assert_artifacts_store_raises(self, store, run_path=None):
        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_sidecar_container(
                container_id=MAIN_JOB_CONTAINER,
                plugins=V1Plugins.get_or_create(
                    V1Plugins(collect_logs=True, collect_artifacts=False)
                ),
                env=None,
                polyaxon_sidecar=V1PolyaxonSidecarContainer(
                    image="sidecar/sidecar",
                    image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                    sleep_interval=213,
                    sync_interval=213,
                ),
                artifacts_store=store,
                run_path=run_path,
            )

    def test_get_main_container_with_logs_store_with_wrong_paths_raises(self):
        artifacts_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
        )
        self.assert_artifacts_store_raises(store=artifacts_store)

        artifacts_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(volume_claim="foo", mount_path="/foo"),
        )
        self.assert_artifacts_store_raises(store=artifacts_store)

    def test_get_sidecar_container_without_an_artifacts_store(self):
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=None,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=213,
            ),
            artifacts_store=None,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path=None,
        )
        assert sidecar is None

    def test_get_sidecar_container_with_non_managed_mount_outputs_logs_store(self):
        env_vars = [
            self.converter._get_env_var(name="key1", value="value1"),
            self.converter._get_env_var(name="key2", value="value2"),
        ]
        mount_non_managed_store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                volume_claim="test", mount_path="/tmp", read_only=True
            ),
        )
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=-1,
            ),
            artifacts_store=mount_non_managed_store,
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_logs=False, collect_artifacts=False, auth=True)
            ),
            run_path=None,
        )

        assert sidecar is None

    def test_get_sidecar_container_with_non_managed_bucket_artifacts_logs_store(self):
        env_vars = [
            self.converter._get_env_var(name="key1", value="value1"),
            self.converter._get_env_var(name="key2", value="value2"),
        ]
        bucket_non_managed_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
        )
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=-1,
            ),
            artifacts_store=bucket_non_managed_store,
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_logs=False, collect_artifacts=False, auth=True)
            ),
            run_path=None,
        )

        assert sidecar is None

    def test_get_sidecar_container_auth_context(
        self,
    ):
        env_vars = [
            self.converter._get_env_var(name="key1", value="value1"),
            self.converter._get_env_var(name="key2", value="value2"),
        ]
        resource1 = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            is_requested=False,
        )
        bucket_managed_store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
            secret=resource1,
        )

        # Default auth is included
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
        ]

        # Nno auth
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=-212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=False)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.volume_mounts == [
            self.converter._get_artifacts_context_mount(read_only=False)
        ]

    def test_get_sidecar_container_with_managed_bucket_outputs_logs_store_and_env_secret(
        self,
    ):
        env_vars = [
            self.converter._get_env_var(name="key1", value="value1"),
            self.converter._get_env_var(name="key2", value="value2"),
        ]
        resource1 = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            is_requested=False,
        )
        bucket_managed_store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
            secret=resource1,
        )

        # Both logs/outputs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=bucket_managed_store.name,
        ) + self.converter._get_items_from_secret(
            secret=resource1
        ) + self.converter._get_connection_env_var(connection=bucket_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_managed_store]
            )
        ]
        assert sidecar.env_from == []
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
        ]

        # logs and no outputs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=-212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_artifacts=False, auth=True)
            ),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=-212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=bucket_managed_store.name,
        ) + self.converter._get_items_from_secret(
            secret=resource1
        ) + self.converter._get_connection_env_var(connection=bucket_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_managed_store]
            )
        ]
        assert sidecar.env_from == []
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
        ]

        # outputs and no logs
        sidecar = self.converter._get_sidecar_container(
            container_id="test",
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(collect_logs=False, auth=True)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id="test",
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id="test",
            artifacts_store_name=bucket_managed_store.name,
        ) + self.converter._get_items_from_secret(
            secret=resource1
        ) + self.converter._get_connection_env_var(connection=bucket_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_managed_store]
            )
        ]
        assert sidecar.env_from == []
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
        ]

    def test_get_sidecar_container_with_managed_bucket_outputs_logs_store_and_mount_secret(
        self,
    ):
        env_vars = [
            self.converter._get_env_var(name="key1", value="value1"),
            self.converter._get_env_var(name="key2", value="value2"),
        ]
        resource1 = V1ConnectionResource(
            name="test1",
            items=["item1", "item2"],
            mount_path="/path",
            is_requested=False,
        )
        bucket_managed_store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
            secret=resource1,
        )

        # Both logs and outputs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=bucket_managed_store.name,
        ) + self.converter._get_items_from_secret(
            secret=resource1
        ) + self.converter._get_connection_env_var(connection=bucket_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_managed_store]
            )
        ]
        assert sidecar.env_from == []
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
            self.converter._get_mount_from_resource(resource=resource1),
        ]

        # logs and no outputs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_artifacts=False, auth=True)
            ),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=bucket_managed_store.name,
        ) + self.converter._get_items_from_secret(
            secret=resource1
        ) + self.converter._get_connection_env_var(connection=bucket_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_managed_store]
            )
        ]
        assert sidecar.env_from == []
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_mount_from_resource(resource=resource1),
        ]

        # outputs and no logs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(collect_logs=False, auth=True)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=bucket_managed_store.name,
        ) + self.converter._get_items_from_secret(
            secret=resource1
        ) + self.converter._get_connection_env_var(connection=bucket_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_managed_store]
            )
        ]
        assert sidecar.env_from == []
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
            self.converter._get_mount_from_resource(resource=resource1),
        ]

    def test_get_sidecar_container_with_managed_bucket_outputs_logs_store_and_env_from(
        self,
    ):
        env_vars = [
            self.converter._get_env_var(name="key1", value="value1"),
            self.converter._get_env_var(name="key2", value="value2"),
        ]
        resource1 = V1ConnectionResource(name="test1", is_requested=False)
        bucket_managed_store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
            secret=resource1,
        )

        # both logs and outputs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=bucket_managed_store.name,
        ) + self.converter._get_items_from_secret(
            secret=resource1
        ) + self.converter._get_connection_env_var(connection=bucket_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_managed_store]
            )
        ]
        assert sidecar.env_from == [
            self.converter._get_env_from_secret(secret=resource1)
        ]
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
        ]

        # logs and no outputs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_artifacts=False, auth=True)
            ),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=bucket_managed_store.name,
        ) + self.converter._get_items_from_secret(
            secret=resource1
        ) + self.converter._get_connection_env_var(connection=bucket_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_managed_store]
            )
        ]
        assert sidecar.env_from == [
            self.converter._get_env_from_secret(secret=resource1)
        ]
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
        ]

        # outputs and no logs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=bucket_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(collect_logs=False, auth=True)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=bucket_managed_store.name,
        ) + self.converter._get_items_from_secret(
            secret=resource1
        ) + self.converter._get_connection_env_var(connection=bucket_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[bucket_managed_store]
            )
        ]
        assert sidecar.env_from == [
            self.converter._get_env_from_secret(secret=resource1)
        ]
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
        ]

    def test_get_sidecar_container_with_managed_mount_outputs_logs_store(self):
        env_vars = [
            self.converter._get_env_var(name="key1", value="value1"),
            self.converter._get_env_var(name="key2", value="value2"),
        ]
        mount_managed_store = V1Connection(
            name="test_path",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(mount_path="/tmp", host_path="/tmp"),
            secret=None,
        )

        # logs and outputs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=mount_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=mount_managed_store.name,
        ) + self.converter._get_connection_env_var(connection=mount_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[mount_managed_store]
            )
        ]
        assert sidecar.env_from == []
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
            self.converter._get_mount_from_store(store=mount_managed_store),
        ]

        # logs and no outputs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=mount_managed_store,
            plugins=V1Plugins.get_or_create(
                V1Plugins(collect_artifacts=False, auth=True)
            ),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=mount_managed_store.name,
        ) + self.converter._get_connection_env_var(connection=mount_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[mount_managed_store]
            )
        ]
        assert sidecar.env_from == []
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_mount_from_store(store=mount_managed_store),
        ]

        # outputs and no logs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=mount_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(collect_logs=False, auth=True)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=mount_managed_store.name,
        ) + self.converter._get_connection_env_var(connection=mount_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[mount_managed_store]
            )
        ]
        assert sidecar.env_from == []
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
            self.converter._get_mount_from_store(store=mount_managed_store),
        ]

    def test_get_sidecar_container_with_managed_mount_outputs_and_blob_logs_store(self):
        env_vars = [
            self.converter._get_env_var(name="key1", value="value1"),
            self.converter._get_env_var(name="key2", value="value2"),
        ]
        resource1 = V1ConnectionResource(name="test1", is_requested=False)
        blob_managed_store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
            secret=resource1,
        )

        # logs and outputs
        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            env=env_vars,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="sidecar/sidecar",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
                sleep_interval=213,
                sync_interval=212,
            ),
            artifacts_store=blob_managed_store,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path="test",
        )

        assert sidecar.name == SIDECAR_CONTAINER
        assert sidecar.image == "sidecar/sidecar"
        assert sidecar.image_pull_policy == "IfNotPresent"
        assert sidecar.command == ["polyaxon", "sidecar"]
        assert sidecar.args == self.converter._get_sidecar_args(
            container_id=MAIN_JOB_CONTAINER,
            sleep_interval=213,
            sync_interval=212,
            monitor_logs=True,
            monitor_spec=True,
        )
        assert sidecar.env == self.converter._get_sidecar_env_vars(
            env_vars=env_vars,
            container_id=MAIN_JOB_CONTAINER,
            artifacts_store_name=blob_managed_store.name,
        ) + self.converter._get_connection_env_var(connection=blob_managed_store) + [
            self.converter._get_connections_catalog_env_var(
                connections=[blob_managed_store]
            )
        ]
        assert sidecar.env_from == [
            self.converter._get_env_from_secret(secret=resource1)
        ]
        assert sidecar.resources == get_sidecar_resources()
        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
        ]

    def test_get_sidecar_container_host_paths(self):
        artifacts_store = V1Connection(
            name="plx-outputs",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(
                mount_path="/tmp/plx/outputs", host_path="/tmp/plx/outputs"
            ),
        )

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

        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="foo",
                image_pull_policy=PullPolicy.ALWAYS,
                sleep_interval=2,
                sync_interval=212,
            ),
            env=[],
            artifacts_store=artifacts_store,
            plugins=plugins,
            run_path="test",
        )

        assert sidecar.volume_mounts == [
            self.converter._get_auth_context_mount(read_only=True),
            self.converter._get_artifacts_context_mount(read_only=False),
            self.converter._get_mount_from_store(store=artifacts_store),
        ]

    def test_get_sidecar_container_override_sync(self):
        artifacts_store = V1Connection(
            name="plx-outputs",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(
                mount_path="/tmp/plx/outputs", host_path="/tmp/plx/outputs"
            ),
        )

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

        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="foo",
                image_pull_policy=PullPolicy.ALWAYS,
                sleep_interval=2,
                sync_interval=212,
            ),
            env=[],
            artifacts_store=artifacts_store,
            plugins=plugins,
            run_path="test",
        )

        assert sidecar.args == [
            "--container-id=polyaxon-main",
            "--sleep-interval=2",
            "--sync-interval=212",
            "--monitor-logs",
            "--monitor-spec",
        ]

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
            sidecar=V1PolyaxonSidecarContainer(
                sleep_interval=-1,
                sync_interval=-1,
            ),
        )

        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="foo",
                image_pull_policy=PullPolicy.ALWAYS,
                sleep_interval=2,
                sync_interval=212,
            ),
            env=[],
            artifacts_store=artifacts_store,
            plugins=plugins,
            run_path="test",
        )

        assert sidecar.args == [
            "--container-id=polyaxon-main",
            "--sleep-interval=-1",
            "--sync-interval=-1",
            "--monitor-logs",
            "--monitor-spec",
        ]

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
            sidecar=V1PolyaxonSidecarContainer(
                sleep_interval=-1,
                sync_interval=-1,
                monitor_logs=False,
                monitor_spec=False,
            ),
        )

        sidecar = self.converter._get_sidecar_container(
            container_id=MAIN_JOB_CONTAINER,
            polyaxon_sidecar=V1PolyaxonSidecarContainer(
                image="foo",
                image_pull_policy=PullPolicy.ALWAYS,
                sleep_interval=2,
                sync_interval=212,
                monitorLogs=False,
                monitorSpec=False,
            ),
            env=[],
            artifacts_store=artifacts_store,
            plugins=plugins,
            run_path="test",
        )

        assert sidecar.args == [
            "--container-id=polyaxon-main",
            "--sleep-interval=-1",
            "--sync-interval=-1",
        ]
