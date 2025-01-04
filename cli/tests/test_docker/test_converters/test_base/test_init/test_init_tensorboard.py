import pytest
import uuid

from clipped.compact.pydantic import ValidationError

from polyaxon._auxiliaries import V1PolyaxonInitContainer
from polyaxon._connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
)
from polyaxon._containers.names import INIT_TENSORBOARD_CONTAINER_PREFIX
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._contexts import paths as ctx_paths
from polyaxon._flow import V1Plugins
from polyaxon._runner.converter.common import constants
from polyaxon._schemas.types import V1TensorboardType
from tests.test_docker.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestInitTensorboard(BaseConverterTest):
    def test_get_tensorboard_init_container(self):
        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.S3,
            tags=["test", "foo"],
            schema_=V1BucketConnection(bucket="s3//:foo"),
        )
        with self.assertRaises(ValidationError):
            V1TensorboardType(
                port=6006,
                uuids="uuid1,  uuid2",
                use_names=True,
                path_prefix="/path/prefix",
                plugins="plug1, plug2",
            )

        uuids = [uuid.uuid4(), uuid.uuid4()]
        tb_args = V1TensorboardType(
            port=6006,
            uuids=uuids,
            use_names=True,
            path_prefix="/path/prefix",
            plugins="plug1, plug2",
        )
        container = self.converter._get_tensorboard_init_container(
            polyaxon_init=V1PolyaxonInitContainer(image="foo", image_tag=""),
            tb_args=tb_args,
            artifacts_store=store,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=True)),
            run_path=self.converter.run_path,
            run_instance="foo.bar.runs.uuid",
            env=None,
        )
        assert INIT_TENSORBOARD_CONTAINER_PREFIX in container.name
        assert container.image == "foo"
        assert container.command == ["polyaxon", "initializer", "tensorboard"]
        assert container.resources.to_dict() == {"cpus": "1.0", "memory": "0.49G"}
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
        uuids_str = ",".join([u.hex for u in uuids])
        assert container.args == [
            "--context-from=s3//:foo",
            "--context-to={}".format(ctx_paths.CONTEXT_MOUNT_ARTIFACTS),
            "--connection-kind=s3",
            "--port=6006",
            "--uuids={}".format(uuids_str),
            "--use-names",
            "--path-prefix=/path/prefix",
            "--plugins=plug1,plug2",
        ]

        store = V1Connection(
            name="test",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            tags=["test", "foo"],
            schema_=V1ClaimConnection(
                mount_path="/claim/path", volume_claim="claim", read_only=True
            ),
        )
        tb_args = V1TensorboardType(
            port=2222, uuids=uuids[0].hex, use_names=False, plugins="plug1"
        )
        container = self.converter._get_tensorboard_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init/init",
                image_tag="",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            tb_args=tb_args,
            artifacts_store=store,
            plugins=V1Plugins.get_or_create(V1Plugins(auth=False)),
            run_path=self.converter.run_path,
            run_instance="foo.bar.runs.uuid",
            env=None,
        )
        assert INIT_TENSORBOARD_CONTAINER_PREFIX in container.name
        assert container.image == "init/init"
        assert container.command == ["polyaxon", "initializer", "tensorboard"]
        assert container.args == [
            "--context-from=/claim/path",
            "--context-to={}".format(ctx_paths.CONTEXT_MOUNT_ARTIFACTS),
            "--connection-kind=volume_claim",
            "--port=2222",
            "--uuids={}".format(uuids[0].hex),
            "--plugins=plug1",
        ]
        assert container.resources.to_dict() == {"cpus": "1.0", "memory": "0.49G"}
        assert container.volume_mounts == [
            self.converter._get_connections_context_mount(
                name=constants.VOLUME_MOUNT_ARTIFACTS,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
                run_path=self.converter.run_path,
            ),
            self.converter._get_mount_from_store(store=store),
        ]
