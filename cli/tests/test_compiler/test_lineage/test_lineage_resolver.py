import pytest
import tempfile

from polyaxon import settings, types
from polyaxon._auxiliaries import (
    get_default_init_container,
    get_default_sidecar_container,
)
from polyaxon._compiler.lineage import collect_io_artifacts
from polyaxon._compiler.resolver import BaseResolver
from polyaxon._connections import (
    V1BucketConnection,
    V1Connection,
    V1ConnectionKind,
    V1ConnectionResource,
    V1HostConnection,
)
from polyaxon._flow import V1CompiledOperation
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._managers.agent import AgentConfigManager
from polyaxon._polyaxonfile.specs import kinds
from polyaxon._schemas.agent import AgentConfig
from polyaxon._utils.test_utils import BaseTestCase
from traceml.artifacts import V1ArtifactKind


@pytest.mark.compiler_mark
class TestLineageResolver(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.compiled_operation = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": kinds.COMPILED_OPERATION,
                "inputs": [
                    {
                        "name": "param1",
                        "type": "str",
                        "value": "test",
                        "isOptional": "true",
                        "validation": {"minLength": 1},
                    },
                    {
                        "name": "param1",
                        "type": types.IMAGE,
                        "isOptional": "true",
                        "value": "repo1",
                        "connection": "connection1",
                    },
                    {
                        "name": "param1",
                        "type": types.IMAGE,
                        "isOptional": "true",
                        "value": "repo2",
                        "connection": "connection2",
                    },
                ],
                "outputs": [
                    {
                        "name": "repo2",
                        "type": types.IMAGE,
                        "isOptional": "true",
                        "value": "repo3",
                        "connection": "connection1",
                    }
                ],
                "run": {
                    "kind": V1RunKind.JOB,
                    "connections": {"test_s3", "connection1", "connection2"},
                    "container": {"image": "test"},
                },
            }
        )

    def test_collector_without_connections(self):
        artifacts = collect_io_artifacts(
            compiled_operation=self.compiled_operation, connection_by_names={}
        )
        assert len(artifacts) == 3
        assert {a.is_input for a in artifacts} == {True, False}
        assert {a.kind for a in artifacts} == {V1ArtifactKind.DOCKER_IMAGE}
        assert {a.connection for a in artifacts} == {"connection1", "connection2"}
        assert {a.summary.get("image") for a in artifacts} == {
            "repo1",
            "repo2",
            "repo3",
        }

    def test_collector_with_connections(self):
        secret = V1ConnectionResource(
            name="secret2",
            is_requested=True,
        )
        connection1 = V1Connection(
            name="connection1",
            kind=V1ConnectionKind.REGISTRY,
            schema_=V1HostConnection(url="localhost:5000"),
            secret=secret,
        )
        artifacts = collect_io_artifacts(
            compiled_operation=self.compiled_operation,
            connection_by_names={"connection1": connection1},
        )
        assert len(artifacts) == 3
        assert {a.is_input for a in artifacts} == {True, False}
        assert {a.kind for a in artifacts} == {V1ArtifactKind.DOCKER_IMAGE}
        assert {a.connection for a in artifacts} == {"connection1", "connection2"}
        assert {a.summary.get("image") for a in artifacts} == {
            "localhost:5000/repo1",
            "repo2",
            "localhost:5000/repo3",
        }

    def test_resolve_connections_with_invalid_config(self):
        fpath = tempfile.mkdtemp()
        AgentConfigManager.CONFIG_PATH = fpath
        secret1 = V1ConnectionResource(
            name="secret1",
            is_requested=True,
        )
        secret2 = V1ConnectionResource(
            name="secret2",
            is_requested=True,
        )
        artifacts_store = V1Connection(
            name="test_s3",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3//:foo"),
            secret=secret1,
        )
        connection1 = V1Connection(
            name="connection1",
            kind=V1ConnectionKind.REGISTRY,
            schema_=V1HostConnection(url="localhost:5000"),
            secret=secret2,
        )
        connection2 = V1Connection(
            name="connection2",
            kind=V1ConnectionKind.REGISTRY,
        )
        settings.AGENT_CONFIG = AgentConfig(
            namespace="foo",
            artifacts_store=artifacts_store,
            connections=[connection1, connection2],
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
        resolver.resolve_agent_environment()
        assert resolver.namespace == "foo"
        assert resolver.connection_by_names == {
            artifacts_store.name: artifacts_store,
            connection1.name: connection1,
            connection2.name: connection2,
        }
        assert resolver.artifacts_store == artifacts_store
        assert resolver.polyaxon_sidecar == get_default_sidecar_container()
        assert resolver.polyaxon_init == get_default_init_container()
        resolver.resolve_artifacts_lineage()
        assert len(resolver.artifacts) == 3
        AgentConfigManager.CONFIG_PATH = None
