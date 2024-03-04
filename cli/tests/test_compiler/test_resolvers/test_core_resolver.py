import pytest
import tempfile

from polyaxon import settings
from polyaxon._auxiliaries import (
    get_default_init_container,
    get_default_sidecar_container,
)
from polyaxon._compiler.resolver import BaseResolver
from polyaxon._connections import (
    V1BucketConnection,
    V1Connection,
    V1ConnectionKind,
    V1ConnectionResource,
)
from polyaxon._flow import V1CompiledOperation
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._managers.agent import AgentConfigManager
from polyaxon._polyaxonfile.specs import kinds
from polyaxon._schemas.agent import AgentConfig
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonCompilerError


@pytest.mark.compiler_mark
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
            resolver.resolve_agent_environment()

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
        secret1 = V1ConnectionResource(
            name="secret1",
            is_requested=True,
        )
        secret2 = V1ConnectionResource(
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
        resolver.resolve_agent_environment()
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
        resolver.resolve_agent_environment()
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
        resolver.resolve_agent_environment()
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
        AgentConfigManager.CONFIG_PATH = None
