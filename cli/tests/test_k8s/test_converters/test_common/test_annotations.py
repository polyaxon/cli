import pytest

from polyaxon._connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
    V1HostPathConnection,
)
from polyaxon._flow import V1Init
from polyaxon._k8s.converter.common.annotations import get_connection_annotations
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
class TestAnnotations(BaseTestCase):
    def test_get_annotations_from_connection(self):
        # No connections
        assert (
            get_connection_annotations(
                artifacts_store=None,
                init_connections=None,
                connections=None,
                connection_by_names=None,
            )
            == {}
        )
        assert (
            get_connection_annotations(
                artifacts_store=None,
                init_connections=[],
                connections=[],
                connection_by_names={},
            )
            == {}
        )

        # Store
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
        )
        assert (
            get_connection_annotations(
                artifacts_store=store,
                init_connections=None,
                connections=None,
                connection_by_names={store.name: store},
            )
            == {}
        )

        store.annotations = {"foo": "bar"}
        assert (
            get_connection_annotations(
                artifacts_store=store,
                init_connections=None,
                connections=None,
                connection_by_names={store.name: store},
            )
            == store.annotations
        )

        # Add connections
        init_conn = V1Connection(
            name="init",
            kind=V1ConnectionKind.SLACK,
            annotations={"init1_key1": "val1", "init1_key2": "val2"},
        )
        init = V1Init(connection="init")
        conn1 = V1Connection(
            name="conn1",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/tmp", volume_claim="test", read_only=True
            ),
            annotations={"conn1_key1": "val1", "conn1_key2": "val2"},
        )
        conn2 = V1Connection(
            name="conn2",
            kind=V1ConnectionKind.HOST_PATH,
            schema_=V1HostPathConnection(
                mount_path="/tmp", host_path="/tmp", read_only=True
            ),
            annotations={"conn2_key1": "val1", "conn2_key2": "val2"},
        )
        assert get_connection_annotations(
            artifacts_store=store,
            init_connections=[init],
            connections=[conn1.name, conn2.name],
            connection_by_names={
                store.name: store,
                init_conn.name: init_conn,
                conn1.name: conn1,
                conn2.name: conn2,
            },
        ) == dict(
            **store.annotations,
            **init_conn.annotations,
            **conn1.annotations,
            **conn2.annotations,
        )
