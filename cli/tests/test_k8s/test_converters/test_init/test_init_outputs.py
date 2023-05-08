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

import pytest

from polyaxon.auxiliaries import V1PolyaxonInitContainer
from polyaxon.connections import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionKind,
)
from polyaxon.containers.names import (
    INIT_ARTIFACTS_CONTAINER_PREFIX,
    generate_container_name,
)
from polyaxon.containers.pull_policy import PullPolicy
from polyaxon.contexts import paths as ctx_paths
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.k8s import k8s_schemas
from polyaxon.k8s.converter.common.mounts import get_artifacts_context_mount
from polyaxon.k8s.converter.init.artifacts import (
    get_artifacts_path_container,
    init_artifact_context_args,
)
from polyaxon.k8s.converter.init.store import get_base_store_container, get_volume_args
from polyaxon.runner.converter.init.artifacts import get_artifacts_store_args
from polyaxon.schemas.types import V1ArtifactsType
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.converter_mark
class TestInitOutputsStore(BaseTestCase):
    def test_get_artifacts_store_args(self):
        assert get_artifacts_store_args(artifacts_path="/some/path", clean=True) == (
            'if [ ! -d "/some/path" ]; then mkdir -m 0777 -p /some/path; fi; '
            'if [ -d /some/path ] && [ "$(ls -A /some/path)" ]; '
            "then rm -R /some/path/*; fi;"
        )

    def test_get_artifacts_path_container_with_none_values(self):
        with self.assertRaises(PolyaxonConverterError):
            get_artifacts_path_container(
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
        container = get_artifacts_path_container(
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

        assert container == get_base_store_container(
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
            volume_mounts=[get_artifacts_context_mount()],
            args=[" ".join(init_args)],
        )

    def test_get_artifacts_path_container_with_managed_mount_store(self):
        store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(mount_path="/claim/path", volume_claim="claim"),
        )
        container = get_artifacts_path_container(
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

        assert container == get_base_store_container(
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
            volume_mounts=[get_artifacts_context_mount()],
            args=[" ".join(init_args)],
        )

    def test_get_artifacts_path_container_with_non_managed_mount_store(self):
        store = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(mount_path="/claim/path", volume_claim="claim"),
        )
        container = get_artifacts_path_container(
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

        assert container == get_base_store_container(
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
            volume_mounts=[get_artifacts_context_mount()],
            args=[" ".join(init_args)],
        )

        container = get_artifacts_path_container(
            polyaxon_init=V1PolyaxonInitContainer(
                image="init",
                image_pull_policy=PullPolicy.IF_NOT_PRESENT,
            ),
            artifacts_store=store,
            run_path="run_uid",
            auto_resume=False,
        )

        init_args = init_artifact_context_args("run_uid")
        assert container == get_base_store_container(
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
            volume_mounts=[get_artifacts_context_mount()],
            args=[" ".join(init_args)],
        )
