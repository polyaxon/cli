from polyaxon import settings
from polyaxon._auxiliaries import V1DefaultScheduling, V1PolyaxonInitContainer
from polyaxon._connections import V1BucketConnection, V1Connection, V1ConnectionKind
from polyaxon._flow.operations.compiled_operation import V1CompiledOperation
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.converters.helpers import CleanerConverter
from polyaxon._k8s.converter.converters.job import JobConverter
from polyaxon._k8s.converter.converters.kubeflow import PytorchJobConverter
from tests.test_k8s.test_converters.base import BaseConverterTest


CONTAINER = {"name": "main", "image": "foo/main", "command": ["train"]}


class TestDefaultSecurityContext(BaseConverterTest):
    def setUp(self):
        super().setUp()
        self.default = k8s_schemas.V1PodSecurityContext(
            run_as_user=2222,
            run_as_group=2222,
            fs_group=2222,
            fs_group_change_policy="OnRootMismatch",
        )
        settings.AGENT_CONFIG.default_scheduling = V1DefaultScheduling(
            security_context=self.default
        )

    @staticmethod
    def get_resource(converter_type, run):
        store = V1Connection(
            name="store",
            kind=V1ConnectionKind.S3,
            schema_=V1BucketConnection(bucket="s3://artifacts"),
        )
        converter = converter_type(
            owner_name="owner-name",
            project_name="project-name",
            run_name="run-name",
            run_uuid="run_uuid",
            polyaxon_init=V1PolyaxonInitContainer(image="foo/init"),
        )
        operation = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": "compiled_operation",
                "plugins": {
                    "auth": False,
                    "docker": False,
                    "shm": False,
                    "tmux": False,
                    "collectArtifacts": False,
                    "collectLogs": False,
                    "collectResources": False,
                    "mountArtifactsStore": False,
                },
                "run": run,
            }
        )
        return converter.get_resource(
            # The agent receives compiled operations as JSON
            compiled_operation=V1CompiledOperation.read(operation.to_json()),
            artifacts_store=store,
            connection_by_names={store.name: store},
            secrets=[],
            config_maps=[],
        )

    def get_job_context(self, environment=None):
        run = {"kind": V1RunKind.JOB, "container": CONTAINER}
        if environment:
            run["environment"] = environment
        resource = self.get_resource(JobConverter, run)
        return resource["batchJobSpec"]["template"].spec.security_context

    def test_job_uses_agent_default(self):
        assert self.get_job_context() == self.default

    def test_cleaner_uses_agent_default(self):
        resource = self.get_resource(
            CleanerConverter,
            {
                "kind": V1RunKind.CLEANER,
                "environment": {"nodeSelector": {"polyaxon": "core"}},
                "container": CONTAINER,
            },
        )
        spec = resource["batchJobSpec"]["template"].spec
        assert spec.security_context == self.default
        assert spec.node_selector == {"polyaxon": "core"}

    def test_distributed_replicas_resolve_their_own_context(self):
        resource = self.get_resource(
            PytorchJobConverter,
            {
                "kind": V1RunKind.PYTORCHJOB,
                "master": {"replicas": 1, "container": CONTAINER},
                "worker": {
                    "replicas": 2,
                    "environment": {"securityContext": {"runAsUser": 1000}},
                    "container": CONTAINER,
                },
            },
        )
        replicas = resource["pytorchJobSpec"]["replicaSpecs"]
        assert replicas["Master"]["template"].spec.security_context == self.default
        assert replicas["Worker"]["template"].spec.security_context == (
            k8s_schemas.V1PodSecurityContext(run_as_user=1000)
        )

    def test_run_context_wins_unchanged(self):
        for context, expected in (
            (
                {"runAsUser": 1000, "runAsGroup": 3000},
                k8s_schemas.V1PodSecurityContext(run_as_user=1000, run_as_group=3000),
            ),
            ({"runAsUser": 0}, k8s_schemas.V1PodSecurityContext(run_as_user=0)),
        ):
            with self.subTest(context=context):
                assert self.get_job_context({"securityContext": context}) == expected

    def test_empty_run_context_is_kept(self):
        assert self.get_job_context({"securityContext": {}}) == {}

    def test_no_agent_default(self):
        for scheduling in (
            None,
            V1DefaultScheduling(node_selector={"polyaxon": "core"}),
        ):
            with self.subTest(scheduling=scheduling):
                settings.AGENT_CONFIG.default_scheduling = scheduling
                assert self.get_job_context() is None
