import pytest

from polyaxon._auxiliaries import V1PolyaxonInitContainer
from polyaxon._connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
)
from polyaxon._containers.names import (
    INIT_ARTIFACTS_CONTAINER_PREFIX,
    generate_container_name,
)
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._contexts import paths as ctx_paths
from polyaxon._k8s import k8s_schemas
from polyaxon._runner.converter.init.artifacts import init_artifact_context_args
from polyaxon._runner.converter.init.store import get_volume_args
from polyaxon._schemas.types import V1ArtifactsType
from polyaxon.exceptions import PolyaxonConverterError
from tests.test_k8s.test_converters.base import BaseConverterTest


@pytest.mark.converter_mark
class TestInitOutputsStore(BaseConverterTest):
    def test_get_artifacts_path_container_with_none_values(self):
        with self.assertRaises(PolyaxonConverterError):
            self.converter._get_artifacts_path_init_container(
                polyaxon_init=V1PolyaxonInitContainer(),
                artifacts_store=None,
                run_path="",
                auto_resume=True,
            )

    def test_get_artifacts_path_container_with_bucket_store(self):
        store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gs//:foo"),
        )
        container = self.converter._get_artifacts_path_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            artifacts_store=store,
            run_path="run_uid",
            auto_resume=True,
        )

        init_args = init_artifact_context_args("run_uid")
        init_args.append(
            get_volume_args(
                store=store,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
                artifacts=V1ArtifactsType(dirs=["run_uid"]),
                paths=None,
                sync_fw=True,
            )
        )

        assert container == self.converter._get_base_store_container(
            container=k8s_schemas.V1Container(name="default"),
            container_name=generate_container_name(
                INIT_ARTIFACTS_CONTAINER_PREFIX, "default", False
            ),
            polyaxon_init=V1PolyaxonInitContainer(
                image="init",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            store=store,
            env=[],
            env_from=[],
            volume_mounts=[self.converter._get_artifacts_context_mount()],
            args=[" ".join(init_args)],
        )

    def test_get_artifacts_path_container_with_managed_mount_store(self):
        store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(mount_path="/claim/path", volume_claim="claim"),
        )
        container = self.converter._get_artifacts_path_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            artifacts_store=store,
            run_path="run_uid",
            auto_resume=True,
        )

        init_args = init_artifact_context_args("run_uid")
        init_args.append(
            get_volume_args(
                store=store,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
                artifacts=V1ArtifactsType(dirs=["run_uid"]),
                paths=None,
                sync_fw=True,
            )
        )

        assert container == self.converter._get_base_store_container(
            container=k8s_schemas.V1Container(name="default"),
            container_name=generate_container_name(
                INIT_ARTIFACTS_CONTAINER_PREFIX, "default", False
            ),
            polyaxon_init=V1PolyaxonInitContainer(
                image="init",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            store=store,
            env=[],
            env_from=[],
            volume_mounts=[self.converter._get_artifacts_context_mount()],
            args=[" ".join(init_args)],
        )

    def test_get_artifacts_path_container_with_non_managed_mount_store(self):
        store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(mount_path="/claim/path", volume_claim="claim"),
        )
        container = self.converter._get_artifacts_path_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            artifacts_store=store,
            run_path="run_uid",
            auto_resume=True,
        )

        init_args = init_artifact_context_args("run_uid")
        init_args.append(
            get_volume_args(
                store=store,
                mount_path=ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
                artifacts=V1ArtifactsType(dirs=["run_uid"]),
                paths=None,
                sync_fw=True,
            )
        )

        assert container == self.converter._get_base_store_container(
            container=k8s_schemas.V1Container(name="init"),
            container_name=generate_container_name(
                INIT_ARTIFACTS_CONTAINER_PREFIX, "default", False
            ),
            polyaxon_init=V1PolyaxonInitContainer(
                image="init",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            store=store,
            env=[],
            env_from=[],
            volume_mounts=[self.converter._get_artifacts_context_mount()],
            args=[" ".join(init_args)],
        )

        container = self.converter._get_artifacts_path_init_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            artifacts_store=store,
            run_path="run_uid",
            auto_resume=False,
        )

        init_args = init_artifact_context_args("run_uid")
        assert container == self.converter._get_base_store_container(
            container=k8s_schemas.V1Container(name="init"),
            container_name=generate_container_name(
                INIT_ARTIFACTS_CONTAINER_PREFIX, "default", False
            ),
            polyaxon_init=V1PolyaxonInitContainer(
                image="init",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            store=store,
            env=[],
            env_from=[],
            volume_mounts=[self.converter._get_artifacts_context_mount()],
            args=[" ".join(init_args)],
        )
