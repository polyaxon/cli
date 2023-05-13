import pytest

from polyaxon.connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1ConnectionResource,
)
from polyaxon.env_vars.keys import (
    EV_KEYS_ARTIFACTS_STORE_NAME,
    EV_KEYS_COLLECT_ARTIFACTS,
    EV_KEYS_COLLECT_RESOURCES,
)
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.polyflow import V1Plugins
from polyaxon.services.values import PolyaxonServices
from tests.test_docker.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestMainEnvVars(BaseConverterTest):
    def setUp(self):
        super().setUp()
        # Secrets
        self.resource1 = V1ConnectionResource(
            name="non_mount_test1",
            items=["item1", "item2"],
            is_requested=False,
        )
        self.resource2 = V1ConnectionResource(
            name="non_mount_test2",
            is_requested=False,
        )

        self.resource3 = V1ConnectionResource(
            name="non_mount_test1",
            items=["item1", "item2"],
            is_requested=True,
        )
        self.resource4 = V1ConnectionResource(
            name="non_mount_test2",
            is_requested=True,
        )

        self.resource5 = V1ConnectionResource(
            name="non_mount_test2",
            is_requested=True,
        )

        self.resource6 = V1ConnectionResource(
            name="mount_test",
            mount_path="/test",
            is_requested=True,
        )
        # Connections
        self.bucket_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
            secret=self.resource3,
        )
        self.mount_store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
        )

    def test_get_env_vars(self):
        assert self.converter._get_main_env_vars(
            plugins=None,
            kv_env_vars=None,
            artifacts_store_name=None,
            connections=None,
            secrets=None,
            config_maps=None,
        ) == self.converter._get_service_env_vars(
            service_header=PolyaxonServices.RUNNER,
            external_host=False,
            log_level=None,
        )

    def test_get_env_vars_with_kv_env_vars(self):
        # Check wrong kv env vars
        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_main_env_vars(
                plugins=None,
                kv_env_vars=["x", "y", "z"],
                artifacts_store_name=None,
                connections=None,
                secrets=None,
                config_maps=None,
            )
        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_main_env_vars(
                plugins=None,
                kv_env_vars={"x": "y"},
                artifacts_store_name=None,
                connections=None,
                secrets=None,
                config_maps=None,
            )

        # Valid kv env vars
        base_env = self.converter._get_service_env_vars(
            service_header=PolyaxonServices.RUNNER,
            external_host=False,
            log_level=None,
        )
        assert self.converter._get_main_env_vars(
            plugins=None,
            kv_env_vars=[["key1", "val1"], ["key2", "val2"]],
            artifacts_store_name=None,
            connections=None,
            secrets=None,
            config_maps=None,
        ) == base_env + self.converter._get_kv_env_vars(
            [["key1", "val1"], ["key2", "val2"]]
        )

    def test_get_env_vars_with_artifacts_store(self):
        base_env = self.converter._get_service_env_vars(
            service_header=PolyaxonServices.RUNNER,
            external_host=False,
            log_level=None,
        )
        assert (
            self.converter._get_main_env_vars(
                plugins=None,
                kv_env_vars=None,
                artifacts_store_name=None,
                connections=None,
                secrets=None,
                config_maps=None,
            )
            == base_env
        )

        assert self.converter._get_main_env_vars(
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    collect_logs=False, collect_artifacts=True, collect_resources=True
                )
            ),
            kv_env_vars=None,
            artifacts_store_name=None,
            connections=None,
            secrets=None,
            config_maps=None,
        ) == base_env + [
            self.converter._get_env_var(name=EV_KEYS_COLLECT_ARTIFACTS, value=True),
            self.converter._get_env_var(name=EV_KEYS_COLLECT_RESOURCES, value=True),
        ]

        assert (
            self.converter._get_main_env_vars(
                plugins=V1Plugins.get_or_create(
                    V1Plugins(
                        collect_logs=False,
                        collect_artifacts=False,
                        collect_resources=False,
                    )
                ),
                kv_env_vars=None,
                artifacts_store_name=None,
                connections=None,
                secrets=None,
                config_maps=None,
            )
            == base_env
        )

        assert (
            self.converter._get_main_env_vars(
                plugins=None,
                kv_env_vars=None,
                artifacts_store_name=None,
                connections=None,
                secrets=None,
                config_maps=None,
            )
            == base_env
        )

        assert self.converter._get_main_env_vars(
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    collect_logs=False,
                    collect_artifacts=True,
                    collect_resources=False,
                )
            ),
            kv_env_vars=None,
            artifacts_store_name=None,
            connections=None,
            secrets=None,
            config_maps=None,
        ) == base_env + [
            self.converter._get_env_var(name=EV_KEYS_COLLECT_ARTIFACTS, value=True)
        ]

    def test_get_env_vars_with_secrets(self):
        base_env = self.converter._get_service_env_vars(
            service_header=PolyaxonServices.RUNNER,
            external_host=False,
            log_level=None,
        )
        assert self.converter._get_main_env_vars(
            plugins=None,
            kv_env_vars=None,
            artifacts_store_name=None,
            connections=None,
            secrets=[self.resource1, self.resource2],
            config_maps=None,
        ) == base_env + self.converter._get_items_from_json_resource(
            resource=self.resource1
        ) + self.converter._get_items_from_json_resource(
            resource=self.resource2
        )

        assert self.converter._get_main_env_vars(
            plugins=None,
            kv_env_vars=None,
            artifacts_store_name=None,
            connections=None,
            secrets=[
                self.resource1,
                self.resource2,
                self.resource3,
                self.resource4,
            ],
            config_maps=None,
        ) == base_env + self.converter._get_items_from_json_resource(
            resource=self.resource1
        ) + self.converter._get_items_from_json_resource(
            resource=self.resource2
        ) + self.converter._get_items_from_json_resource(
            resource=self.resource3
        ) + self.converter._get_items_from_json_resource(
            resource=self.resource4
        )

    def test_get_env_vars_with_config_maps(self):
        base_env = self.converter._get_service_env_vars(
            service_header=PolyaxonServices.RUNNER,
            external_host=False,
            log_level=None,
        )
        assert self.converter._get_main_env_vars(
            plugins=None,
            kv_env_vars=None,
            artifacts_store_name=None,
            connections=None,
            secrets=None,
            config_maps=[self.resource1, self.resource2],
        ) == base_env + self.converter._get_items_from_json_resource(
            resource=self.resource1
        ) + self.converter._get_items_from_json_resource(
            resource=self.resource2
        )

        assert self.converter._get_main_env_vars(
            plugins=None,
            kv_env_vars=None,
            artifacts_store_name=None,
            connections=None,
            secrets=None,
            config_maps=[
                self.resource1,
                self.resource2,
                self.resource3,
                self.resource4,
            ],
        ) == base_env + self.converter._get_items_from_json_resource(
            resource=self.resource1
        ) + self.converter._get_items_from_json_resource(
            resource=self.resource2
        ) + self.converter._get_items_from_json_resource(
            resource=self.resource3
        ) + self.converter._get_items_from_json_resource(
            resource=self.resource4
        )

    def test_get_env_vars_with_all(self):
        connection = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
            secret=self.resource6,
        )

        env_vars = self.converter._get_main_env_vars(
            plugins=V1Plugins.get_or_create(
                V1Plugins(
                    collect_logs=False, collect_artifacts=True, collect_resources=True
                )
            ),
            kv_env_vars=[["key1", "val1"], ["key2", "val2"]],
            artifacts_store_name="test",
            connections=[connection],
            secrets=[
                self.resource1,
                self.resource2,
                self.resource3,
                self.resource4,
                self.resource6,
            ],
            config_maps=[
                self.resource1,
                self.resource2,
                self.resource3,
                self.resource4,
            ],
        )
        expected = self.converter._get_service_env_vars(
            service_header=PolyaxonServices.RUNNER,
            external_host=False,
            log_level=None,
        )
        expected += [
            self.converter._get_env_var(name=EV_KEYS_COLLECT_ARTIFACTS, value=True),
            self.converter._get_env_var(name=EV_KEYS_COLLECT_RESOURCES, value=True),
            self.converter._get_env_var(
                name=EV_KEYS_ARTIFACTS_STORE_NAME, value="test"
            ),
        ]
        expected += self.converter._get_connection_env_var(connection=connection)
        expected += [
            self.converter._get_connections_catalog_env_var(connections=[connection])
        ]
        expected += self.converter._get_kv_env_vars(
            [["key1", "val1"], ["key2", "val2"]]
        )
        expected += self.converter._get_env_vars_from_k8s_resources(
            secrets=[
                self.resource1,
                self.resource2,
                self.resource3,
                self.resource4,
                self.resource6,
            ],
            config_maps=[
                self.resource1,
                self.resource2,
                self.resource3,
                self.resource4,
            ],
        )

        assert env_vars == expected
