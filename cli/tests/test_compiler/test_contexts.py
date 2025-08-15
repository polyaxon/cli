import pytest

from clipped.utils.tz import now

from polyaxon._compiler.contexts import resolve_contexts
from polyaxon._connections import V1ClaimConnection, V1Connection, V1ConnectionKind
from polyaxon._contexts import paths as ctx_paths
from polyaxon._flow import V1CloningKind, V1CompiledOperation, V1RunKind
from polyaxon._polyaxonfile.specs import kinds
from polyaxon._utils.test_utils import BaseTestCase


class V1CloningKin(object):
    pass


@pytest.mark.compiler_mark
class TestResolveContexts(BaseTestCase):
    def test_resolver_default_contexts(self):
        context_root = ctx_paths.CONTEXT_ROOT
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
                "run": {"kind": V1RunKind.JOB, "container": {"image": "test"}},
            }
        )
        spec = resolve_contexts(
            namespace="test",
            owner_name="user",
            project_name="project",
            project_uuid="uuid",
            run_uuid="uuid",
            run_name="run",
            run_path="test",
            compiled_operation=compiled_operation,
            artifacts_store=None,
            connection_by_names={},
            iteration=None,
            created_at=None,
            compiled_at=None,
            username="user",
            user_email="user@local.com",
        )
        assert spec == {
            "globals": {
                "owner_name": "user",
                "project_unique_name": "user.project",
                "project_name": "project",
                "project_uuid": "uuid",
                "run_info": "user.project.runs.uuid",
                "context_path": context_root,
                "artifacts_path": "{}/artifacts".format(context_root),
                "name": "run",
                "uuid": "uuid",
                "namespace": "test",
                "iteration": None,
                "created_at": None,
                "compiled_at": None,
                "schedule_at": None,
                "started_at": None,
                "finished_at": None,
                "duration": None,
                "cloning_kind": None,
                "original_uuid": None,
                "is_independent": True,
                "store_path": "",
                "username": "user",
                "user_email": "user@local.com",
                "run_relative_outputs_path": "test/outputs",
            },
            "init": {},
            "connections": {},
        }

    def test_resolver_init_and_connections_contexts(self):
        context_root = ctx_paths.CONTEXT_ROOT
        store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/claim/path", volume_claim="claim", read_only=True
            ),
        )

        compiled_operation = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": kinds.COMPILED_OPERATION,
                "plugins": {
                    "auth": False,
                    "shm": False,
                    "mountArtifactsStore": True,
                    "collectLogs": False,
                    "collectArtifacts": False,
                    "collectResources": False,
                },
                "run": {
                    "kind": V1RunKind.JOB,
                    "container": {"image": "test"},
                    "connections": [store.name],
                    "init": [{"connection": store.name}],
                },
            }
        )
        date_value = now()
        spec = resolve_contexts(
            namespace="test",
            owner_name="user",
            project_name="project",
            project_uuid="uuid",
            run_uuid="uuid",
            run_name="run",
            run_path="test",
            compiled_operation=compiled_operation,
            artifacts_store=store,
            connection_by_names={store.name: store},
            iteration=12,
            created_at=date_value,
            compiled_at=date_value,
            cloning_kind=V1CloningKind.COPY,
            original_uuid="uuid-copy",
            is_independent=False,
        )
        assert spec == {
            "globals": {
                "owner_name": "user",
                "project_unique_name": "user.project",
                "project_name": "project",
                "project_uuid": "uuid",
                "name": "run",
                "uuid": "uuid",
                "context_path": context_root,
                "artifacts_path": "{}/artifacts".format(context_root),
                "run_artifacts_path": "/claim/path/test",
                "run_outputs_path": "/claim/path/test/outputs",
                "run_relative_outputs_path": "test/outputs",
                "namespace": "test",
                "iteration": 12,
                "run_info": "user.project.runs.uuid",
                "created_at": date_value,
                "compiled_at": date_value,
                "schedule_at": None,
                "started_at": None,
                "finished_at": None,
                "duration": None,
                "is_independent": False,
                "username": None,
                "user_email": None,
                "cloning_kind": V1CloningKind.COPY,
                "original_uuid": "uuid-copy",
                "store_path": "/claim/path",
            },
            "init": {"test_claim": store.schema_.to_dict()},
            "connections": {"test_claim": store.schema_.to_dict()},
        }

    def test_resolver_outputs_collections(self):
        context_root = ctx_paths.CONTEXT_ROOT
        store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/claim/path", volume_claim="claim", read_only=True
            ),
        )
        compiled_operation = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": kinds.COMPILED_OPERATION,
                "plugins": {
                    "auth": False,
                    "shm": False,
                    "mountArtifactsStore": False,
                    "collectLogs": False,
                    "collectArtifacts": True,
                    "collectResources": True,
                },
                "run": {
                    "kind": V1RunKind.JOB,
                    "container": {"image": "test"},
                    "connections": [store.name],
                    "init": [{"connection": store.name}],
                },
            }
        )
        spec = resolve_contexts(
            namespace="test",
            owner_name="user",
            project_name="project",
            project_uuid="uuid",
            run_uuid="uuid",
            run_name="run",
            run_path="test",
            compiled_operation=compiled_operation,
            artifacts_store=store,
            connection_by_names={store.name: store},
            iteration=12,
            created_at=None,
            compiled_at=None,
            is_independent=True,
        )
        assert spec == {
            "globals": {
                "owner_name": "user",
                "project_name": "project",
                "project_unique_name": "user.project",
                "project_uuid": "uuid",
                "name": "run",
                "uuid": "uuid",
                "run_info": "user.project.runs.uuid",
                "context_path": context_root,
                "artifacts_path": "{}/artifacts".format(context_root),
                "run_artifacts_path": "{}/artifacts/test".format(context_root),
                "run_outputs_path": "{}/artifacts/test/outputs".format(context_root),
                "run_relative_outputs_path": "test/outputs",
                "namespace": "test",
                "iteration": 12,
                "created_at": None,
                "compiled_at": None,
                "schedule_at": None,
                "started_at": None,
                "finished_at": None,
                "duration": None,
                "cloning_kind": None,
                "original_uuid": None,
                "is_independent": True,
                "username": None,
                "user_email": None,
                "store_path": "",
            },
            "init": {"test_claim": store.schema_.to_dict()},
            "connections": {"test_claim": store.schema_.to_dict()},
        }

    def test_resolver_mount_artifacts_store(self):
        context_root = ctx_paths.CONTEXT_ROOT
        store = V1Connection(
            name="test_claim",
            kind=V1ConnectionKind.VOLUME_CLAIM,
            schema_=V1ClaimConnection(
                mount_path="/claim/path", volume_claim="claim", read_only=True
            ),
        )
        compiled_operation = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": kinds.COMPILED_OPERATION,
                "plugins": {
                    "auth": False,
                    "shm": False,
                    "mountArtifactsStore": True,
                    "collectLogs": False,
                    "collectArtifacts": True,
                    "collectResources": True,
                },
                "run": {
                    "kind": V1RunKind.JOB,
                    "container": {"image": "test"},
                    "connections": [store.name],
                    "init": [{"connection": store.name}],
                },
            }
        )
        spec = resolve_contexts(
            namespace="test",
            owner_name="user",
            project_name="project",
            project_uuid="uuid",
            run_uuid="uuid",
            run_name="run",
            run_path="test",
            compiled_operation=compiled_operation,
            artifacts_store=store,
            connection_by_names={store.name: store},
            iteration=12,
            created_at=None,
            compiled_at=None,
        )
        assert spec == {
            "globals": {
                "owner_name": "user",
                "project_name": "project",
                "project_unique_name": "user.project",
                "project_uuid": "uuid",
                "name": "run",
                "uuid": "uuid",
                "run_info": "user.project.runs.uuid",
                "context_path": context_root,
                "artifacts_path": "{}/artifacts".format(context_root),
                "run_artifacts_path": "{}/artifacts/test".format(context_root),
                "run_outputs_path": "{}/artifacts/test/outputs".format(context_root),
                "run_relative_outputs_path": "test/outputs",
                "namespace": "test",
                "iteration": 12,
                "created_at": None,
                "compiled_at": None,
                "schedule_at": None,
                "started_at": None,
                "finished_at": None,
                "duration": None,
                "cloning_kind": None,
                "original_uuid": None,
                "is_independent": True,
                "username": None,
                "user_email": None,
                "store_path": "/claim/path",
            },
            "init": {"test_claim": store.schema_.to_dict()},
            "connections": {"test_claim": store.schema_.to_dict()},
        }

    def test_resolver_default_service_ports(self):
        context_root = ctx_paths.CONTEXT_ROOT
        compiled_operation = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": kinds.COMPILED_OPERATION,
                "plugins": {
                    "auth": False,
                    "shm": False,
                    "collectLogs": False,
                    "collectArtifacts": True,
                    "collectResources": True,
                },
                "run": {
                    "kind": V1RunKind.SERVICE,
                    "ports": [1212, 1234],
                    "container": {"image": "test", "command": "{{ ports[0] }}"},
                },
            }
        )
        spec = resolve_contexts(
            namespace="test",
            owner_name="user",
            project_name="project",
            project_uuid="uuid",
            run_uuid="uuid",
            run_name="run",
            run_path="test",
            compiled_operation=compiled_operation,
            artifacts_store=None,
            connection_by_names={},
            iteration=12,
            created_at=None,
            compiled_at=None,
        )
        assert spec == {
            "globals": {
                "owner_name": "user",
                "project_name": "project",
                "project_unique_name": "user.project",
                "project_uuid": "uuid",
                "run_info": "user.project.runs.uuid",
                "name": "run",
                "uuid": "uuid",
                "context_path": context_root,
                "artifacts_path": "{}/artifacts".format(context_root),
                "run_artifacts_path": "{}/artifacts/test".format(context_root),
                "run_outputs_path": "{}/artifacts/test/outputs".format(context_root),
                "run_relative_outputs_path": "test/outputs",
                "namespace": "test",
                "iteration": 12,
                "ports": [1212, 1234],
                "base_url": "/services/v1/test/user/project/runs/uuid/1212",
                "base_urls": [
                    "/services/v1/test/user/project/runs/uuid/1212",
                    "/services/v1/test/user/project/runs/uuid/1234",
                ],
                "created_at": None,
                "compiled_at": None,
                "schedule_at": None,
                "started_at": None,
                "finished_at": None,
                "duration": None,
                "cloning_kind": None,
                "original_uuid": None,
                "is_independent": True,
                "username": None,
                "user_email": None,
                "store_path": "",
            },
            "init": {},
            "connections": {},
        }
