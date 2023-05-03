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
import tempfile

from polyaxon import settings
from polyaxon.auxiliaries import (
    get_default_init_container,
    get_default_sidecar_container,
)
from polyaxon.connections import (
    V1BucketConnection,
    V1Connection,
    V1ConnectionKind,
    V1K8sResource,
)
from polyaxon.exceptions import PolyaxonCompilerError
from polyaxon.managers.agent import AgentConfigManager
from polyaxon.polyaxonfile.specs import kinds
from polyaxon.polyflow import V1CompiledOperation, V1RunKind
from polyaxon.compiler.resolver import BaseResolver
from polyaxon.schemas.cli.agent_config import AgentConfig
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.polypod_mark
class TestResolver(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.compiled_operation = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": kinds.COMPILED_OPERATION,
                "plugins": {
                    "auth": False,
                    "shm": False,
                    "collectLogs": False,
                    "collectArtifacts": False,
                    "collectResources": False,
                },
                "run": {"kind": V1RunKind.JOB, "container": {"image": "test"}},
            }
        )

    def test_core_resolver_instance(self):
        resolver = BaseResolver(
            run=None,
            compiled_operation=self.compiled_operation,
            owner_name="user",
            project_name="p1",
            project_uuid=None,
            run_name="j1",
            run_uuid=None,
            run_path="test",
            params=None,
        )

        assert resolver.project_uuid == resolver.project_name
        assert resolver.run_uuid == resolver.run_name

        resolver = BaseResolver(
            run=None,
            compiled_operation=self.compiled_operation,
            owner_name="user",
            project_name="p1",
            run_name="j1",
            run_path="test",
            project_uuid="some_uuid",
            run_uuid="some_uuid",
            params=None,
        )
        assert resolver.project_uuid != resolver.project_name
        assert resolver.run_uuid != resolver.run_name

    def test_resolve_connections_with_no_config(self):
        settings.AGENT_CONFIG = None
        resolver = BaseResolver(
            run=None,
            compiled_operation=self.compiled_operation,
            owner_name="user",
            project_name="p1",
            project_uuid=None,
            run_name="j1",
            run_uuid=None,
            run_path="test",
            params=None,
        )
        with self.assertRaises(PolyaxonCompilerError):
            resolver.resolve_connections()

    def test_resolve_without_compiled_operation(self):
        with self.assertRaises(PolyaxonCompilerError):
            BaseResolver(
                run=None,
                compiled_operation=None,
                owner_name="user",
                project_name="p1",
                project_uuid=None,
                run_name="j1",
                run_uuid=None,
                run_path="test",
                params=None,
            )

    def test_resolve_connections_with_invalid_config(self):
        fpath = tempfile.mkdtemp()
        AgentConfigManager.CONFIG_PATH = fpath
        secret1 = V1K8sResource(
            name="secret1",
            is_requested=True,
        )
        secret2 = V1K8sResource(
            name="secret2",
            is_requested=True,
        )
        connection1 = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
            secret=secret1,
        )
        connection2 = V1Connection(
            name="test_gcs",
            kind=V1ConnectionKind.GCS,
            schema_=V1BucketConnection(bucket="gcs//:foo"),
            secret=secret1,
        )
        connection3 = V1Connection(
            name="test_wasb",
            kind=V1ConnectionKind.WASB,
            schema_=V1BucketConnection(bucket="wasbs//:foo"),
            secret=secret2,
        )
        settings.AGENT_CONFIG = AgentConfig(
            namespace="foo",
            artifacts_store=connection1,
            connections=[connection2, connection3],
        )

        resolver = BaseResolver(
            run=None,
            compiled_operation=self.compiled_operation,
            owner_name="user",
            project_name="p1",
            project_uuid=None,
            run_name="j1",
            run_uuid=None,
            run_path="test",
            params=None,
        )
        resolver.resolve_connections()
        assert resolver.namespace == "foo"
        assert resolver.connection_by_names == {connection1.name: connection1}
        assert resolver.artifacts_store == connection1
        assert resolver.secrets == [
            secret1,
            secret2,
        ]
        assert resolver.polyaxon_sidecar == get_default_sidecar_container()
        assert resolver.polyaxon_init == get_default_init_container()

        # Add run spec to resolve connections
        compiled_operation = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": kinds.COMPILED_OPERATION,
                "plugins": {
                    "auth": False,
                    "shm": False,
                    "collectLogs": False,
                    "collectArtifacts": False,
                    "collectResources": False,
                },
                "run": {
                    "kind": V1RunKind.JOB,
                    "container": {"image": "test"},
                    "connections": {connection3.name},
                },
            }
        )
        resolver = BaseResolver(
            run=None,
            compiled_operation=compiled_operation,
            owner_name="user",
            project_name="p1",
            project_uuid=None,
            run_name="j1",
            run_uuid=None,
            run_path="test",
            params=None,
        )
        resolver.resolve_connections()
        assert resolver.namespace == "foo"
        assert resolver.connection_by_names == {
            connection1.name: connection1,
            connection3.name: connection3,
        }
        assert resolver.secrets == [secret1, secret2]
        assert resolver.artifacts_store == connection1
        assert resolver.polyaxon_sidecar == get_default_sidecar_container()
        assert resolver.polyaxon_init == get_default_init_container()

        # Add run spec to resolve connections
        compiled_operation = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": kinds.COMPILED_OPERATION,
                "plugins": {
                    "auth": False,
                    "shm": False,
                    "collectLogs": False,
                    "collectArtifacts": False,
                    "collectResources": False,
                },
                "run": {
                    "kind": V1RunKind.JOB,
                    "container": {"image": "test"},
                    "connections": {
                        connection1.name,
                        connection2.name,
                        connection3.name,
                    },
                },
            }
        )
        resolver = BaseResolver(
            run=None,
            compiled_operation=compiled_operation,
            owner_name="user",
            project_name="p1",
            project_uuid=None,
            run_name="j1",
            run_uuid=None,
            run_path="test",
            params=None,
        )
        resolver.resolve_connections()
        assert resolver.namespace == "foo"
        assert resolver.connection_by_names == {
            connection3.name: connection3,
            connection2.name: connection2,
            connection1.name: connection1,
        }
        assert resolver.secrets == [
            secret1,
            secret2,
        ]
        assert resolver.artifacts_store == connection1
        assert resolver.polyaxon_sidecar == get_default_sidecar_container()
        assert resolver.polyaxon_init == get_default_init_container()
