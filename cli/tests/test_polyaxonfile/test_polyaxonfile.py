import os
import pytest

from mock import MagicMock, patch

from polyaxon import pkg
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import ENV_KEYS_USE_GIT_REGISTRY
from polyaxon._flow import (
    V1CompiledOperation,
    V1Environment,
    V1GridSearch,
    V1HpChoice,
    V1HpLinSpace,
    V1Hyperband,
    V1Mapping,
    V1MetricEarlyStopping,
    V1Plugins,
    V1RandomSearch,
    V1RunKind,
    V1Termination,
)
from polyaxon._polyaxonfile import check_polyaxonfile
from polyaxon._polyaxonfile.specs import (
    CompiledOperationSpecification,
    OperationSpecification,
)
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonfileError, PolyaxonValidationError
from polyaxon.schemas import V1ProjectVersionKind


@pytest.mark.polyaxonfile_mark
class TestPolyaxonfiles(BaseTestCase):
    def test_missing_version_raises(self):
        with self.assertRaises(PolyaxonfileError):
            check_polyaxonfile(
                polyaxonfile=os.path.abspath(
                    "tests/fixtures/plain/missing_version.yml"
                ),
                is_cli=False,
            )

    def test_non_supported_version_raises(self):
        with self.assertRaises(PolyaxonfileError):
            check_polyaxonfile(
                polyaxonfile=os.path.abspath(
                    "tests/fixtures/plain/non_supported_file.yml"
                ),
                is_cli=False,
            )

    def test_non_existing_raises(self):
        with self.assertRaises(PolyaxonfileError):
            check_polyaxonfile(
                polyaxonfile=os.path.abspath(
                    "tests/fixtures/plain/non_existing_file.yml"
                ),
                is_cli=False,
            )

    def test_missing_kind_raises(self):
        with self.assertRaises(PolyaxonfileError):
            check_polyaxonfile(
                polyaxonfile=os.path.abspath("tests/fixtures/plain/missing_kind.yml"),
                is_cli=False,
            )

    def test_multi_option_call(self):
        with self.assertRaises(PolyaxonfileError):
            check_polyaxonfile(
                hub="component:12", url="http://foo.bar", is_cli=False, to_op=False
            )

    def test_wong_hub_call(self):
        with self.assertRaises(PolyaxonfileError):
            check_polyaxonfile(hub="component:12", is_cli=False, to_op=False)

    def test_from_git_hub(self):
        os.environ[ENV_KEYS_USE_GIT_REGISTRY] = "true"
        with patch(
            "polyaxon._config.spec.ConfigSpec.read_from_public_hub"
        ) as request_mock:
            request_mock.return_value = os.path.abspath(
                "tests/fixtures/plain/simple_job.yml"
            )
            operation = check_polyaxonfile(hub="component:12", is_cli=False, to_op=True)

        assert request_mock.call_count == 1
        assert operation.kind == "operation"
        assert operation.hub_ref == "component:12"
        del os.environ[ENV_KEYS_USE_GIT_REGISTRY]

    def test_from_public_hub(self):
        with patch("polyaxon._sdk.api.ProjectsV1Api.get_version") as request_mock:
            request_mock.return_value = MagicMock(
                kind=V1ProjectVersionKind.COMPONENT,
                content=os.path.abspath("tests/fixtures/plain/simple_job.yml"),
            )
            operation = check_polyaxonfile(hub="component:12", is_cli=False, to_op=True)

        assert request_mock.call_count == 1
        assert operation.kind == "operation"
        assert operation.hub_ref == "component:12"

    def test_from_hub(self):
        with patch("polyaxon._sdk.api.ProjectsV1Api.get_version") as request_mock:
            request_mock.return_value = MagicMock(
                kind=V1ProjectVersionKind.COMPONENT,
                content=os.path.abspath("tests/fixtures/plain/simple_job.yml"),
            )
            operation = check_polyaxonfile(
                hub="org/component:12", is_cli=False, to_op=True
            )
        assert operation.version == pkg.SCHEMA_VERSION
        assert operation.kind == "operation"
        assert operation.hub_ref == "org/component:12"

    def test_simple_file_passes(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/plain/simple_job.yml"),
                {"kind": "compiled_operation"},
            ]
        )

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1
        assert run_config.tags is None
        assert len(run_config.run.volumes) == 1
        assert run_config.run.environment.annotations == {
            "tf-version.cloud-tpus.google.com": "2.2"
        }
        assert run_config.run.to_dict()["volumes"][0] == {
            "name": "foo",
            "secret": {"secretName": "mysecret"},
        }
        assert run_config.run.container.image == "python-with-boto3"
        assert run_config.run.container.command == "python download-s3-bucket"
        assert run_config.run.container.resources == {
            "requests": {"nvidia.com/gpu": 1},
            "limits": {"nvidia.com/gpu": 1},
        }
        assert run_config.run.container.volume_mounts == [
            {"name": "foo", "mount_path": "~/.aws/credentials", "readOnly": True}
        ]

    def test_simple_file_with_run_patch_passes(self):
        op_config = OperationSpecification.read(
            os.path.abspath("tests/fixtures/plain/simple_job_run_patch.yml"),
        )

        assert op_config.version == 1.1
        assert op_config.tags is None
        assert op_config.run_patch["environment"]["annotations"] == {
            "tf-version.cloud-tpus.google.com": "2.2"
        }
        assert len(op_config.component.run.volumes) == 1
        assert op_config.component.run.to_dict()["volumes"][0] == {
            "name": "foo",
            "secret": {"secretName": "mysecret"},
        }
        assert op_config.component.run.container.image == "python-with-boto3"
        assert op_config.component.run.container.command == "python download-s3-bucket"
        assert op_config.component.run.container.resources == {
            "requests": {"nvidia.com/gpu": 1},
            "limits": {"nvidia.com/gpu": 1},
        }
        assert op_config.component.run.container.volume_mounts == [
            {"name": "foo", "mount_path": "~/.aws/credentials", "readOnly": True}
        ]

        run_config = OperationSpecification.compile_operation(op_config)
        assert run_config.version == 1.1
        assert run_config.tags is None
        assert len(run_config.run.volumes) == 1
        assert run_config.run.environment.annotations == {
            "tf-version.cloud-tpus.google.com": "2.2"
        }
        assert run_config.run.to_dict()["volumes"][0] == {
            "name": "foo",
            "secret": {"secretName": "mysecret"},
        }
        assert run_config.run.container.image == "python-with-boto3"
        assert run_config.run.container.command == "python download-s3-bucket"
        assert run_config.run.container.resources == {
            "requests": {"nvidia.com/gpu": 1},
            "limits": {"nvidia.com/gpu": 1},
        }
        assert run_config.run.container.volume_mounts == [
            {"name": "foo", "mount_path": "~/.aws/credentials", "readOnly": True}
        ]

    def test_passing_params_to_no_io_overrides_polyaxonfiles_raises(self):
        with self.assertRaises(PolyaxonfileError):
            check_polyaxonfile(
                polyaxonfile=os.path.abspath("tests/fixtures/plain/simple_job.yml"),
                params={"flag": True, "loss": "some-loss"},
                is_cli=False,
            )

    def test_passing_params_overrides_polyaxonfiles(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/typing/required_inputs.yml"),
                {"kind": "compiled_operation"},
            ]
        )

        with self.assertRaises(PolyaxonValidationError):
            CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.inputs[0].value is None
        assert run_config.inputs[1].value is None
        run_config.apply_params(
            params={"flag": {"value": True}, "loss": {"value": "some-loss"}}
        )
        assert run_config.inputs[0].value == "some-loss"
        assert run_config.inputs[1].value is True
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        run_config = CompiledOperationSpecification.apply_runtime_contexts(run_config)
        assert run_config.version == 1.1
        assert run_config.tags == ["foo", "bar"]
        assert run_config.run.container.image == "my_image"
        assert run_config.run.container.command == ["/bin/sh", "-c"]
        assert (
            run_config.run.container.args
            == "video_prediction_train --loss=some-loss --flag"
        )

    def test_passing_wrong_params_raises(self):
        with self.assertRaises(PolyaxonfileError):
            check_polyaxonfile(
                polyaxonfile=os.path.abspath("tests/fixtures/plain/simple_job.yml"),
                params="foo",
                is_cli=False,
            )

    def test_job_file_with_init_passes(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/plain/job_file_with_init.yml"),
                {"kind": "compiled_operation"},
            ]
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1
        assert isinstance(run_config.plugins, V1Plugins)
        assert run_config.plugins.log_level == "INFO"
        assert run_config.plugins.auth is True
        assert run_config.plugins.shm is True
        assert run_config.plugins.docker is True
        assert run_config.plugins.collect_artifacts is True
        assert run_config.plugins.collect_logs is None
        assert isinstance(run_config.run.environment, V1Environment)
        assert run_config.run.environment.labels == {"key": "value"}
        assert len(run_config.run.init) == 3
        assert len(run_config.run.connections) == 2
        assert run_config.run.connections == ["data1", "data2"]
        assert len(run_config.run.volumes) == 2
        assert run_config.run.volumes[0].name == "my_ssh_secret"
        assert run_config.run.volumes[0].secret == {"secretName": "mysecret"}
        assert run_config.run.volumes[1].name == "config_map"
        assert run_config.run.volumes[1].config_map == {"configName": "config_map2"}

    def test_job_file_with_templated_file_init_and_to_env(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath(
                    "tests/fixtures/plain/job_file_with_templated_file_init_and_to_env.yml"
                ),
                {"kind": "compiled_operation"},
            ]
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1
        assert isinstance(run_config.plugins, V1Plugins)
        assert run_config.plugins.log_level == "INFO"
        assert run_config.plugins.auth is True
        assert run_config.plugins.shm is True
        assert run_config.plugins.docker is True
        assert run_config.plugins.collect_artifacts is True
        assert run_config.plugins.collect_logs is None
        assert isinstance(run_config.run.environment, V1Environment)
        assert run_config.run.environment.labels == {"key": "value"}
        assert len(run_config.run.init) == 4
        assert "param1" in run_config.run.init[0].file.content
        assert "param2" in run_config.run.init[0].file.content
        assert "params.dest.connection" in run_config.run.init[0].file.content
        assert "23423" not in run_config.run.init[0].file.content
        assert "foo" not in run_config.run.init[0].file.content
        assert (
            "https://registry.com/image:tag" not in run_config.run.init[0].file.content
        )
        assert len(run_config.run.connections) == 2
        assert run_config.run.connections == ["data1", "data2"]
        assert len(run_config.run.volumes) == 2
        assert run_config.run.volumes[0].name == "my_ssh_secret"
        assert run_config.run.volumes[0].secret == {"secretName": "mysecret"}
        assert run_config.run.volumes[1].name == "config_map"
        assert run_config.run.volumes[1].config_map == {"configName": "config_map2"}

        # Compile run
        run_config = CompiledOperationSpecification.apply_runtime_contexts(
            run_config,
            contexts={"connections": {"registry": {"url": "https://registry.com"}}},
        )
        assert "param1" not in run_config.run.init[0].file.content
        assert "param2" not in run_config.run.init[0].file.content
        assert "params.dest.connection" not in run_config.run.init[0].file.content
        assert "23423" in run_config.run.init[0].file.content
        assert "foo" in run_config.run.init[0].file.content
        assert "https://registry.com/image:tag" in run_config.run.init[0].file.content

    def test_job_file_with_termination_passes(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/plain/job_file_with_termination.yml"),
                {"kind": "compiled_operation"},
            ]
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1
        assert isinstance(run_config.termination, V1Termination)
        assert run_config.termination.max_retries == 5
        assert run_config.termination.timeout == 500
        assert run_config.termination.ttl == 400
        assert run_config.run.environment.restart_policy == "Never"

    def test_job_file_with_environment_passes(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/plain/job_file_with_environment.yml"),
                {"kind": "compiled_operation"},
            ]
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1
        assert isinstance(run_config.run.environment, V1Environment)
        assert run_config.run.environment.node_selector == {"polyaxon.com": "core"}
        assert run_config.run.container.resources == {
            "requests": {"cpu": 1, "memory": 200},
            "limits": {"cpu": 2, "memory": 200},
        }
        assert run_config.run.environment.affinity.node_affinity == {
            "requiredDuringSchedulingIgnoredDuringExecution": {}
        }
        assert run_config.run.environment.tolerations[0].key == "key"
        assert run_config.run.environment.tolerations[0].operator == "Exists"
        assert run_config.run.environment.labels == {
            "label_key1": "val1",
            "label_key2": "val2",
        }
        assert run_config.run.environment.annotations == {
            "annotation_key1": "val1",
            "annotation_key2": "val2",
        }
        assert run_config.run.environment.service_account_name == "new_sa"
        assert run_config.run.environment.image_pull_secrets == ["secret1", "secret2"]
        assert run_config.run.environment.security_context.run_as_user == 1000
        assert run_config.run.environment.security_context.run_as_group == 3000
        assert isinstance(run_config.plugins, V1Plugins)
        assert run_config.plugins.log_level == "DEBUG"

    def test_matrix_file_passes(self):
        plx_file = check_polyaxonfile(
            polyaxonfile=os.path.abspath("tests/fixtures/plain/matrix_job_file.yml"),
            is_cli=False,
        )
        run_config = OperationSpecification.compile_operation(plx_file)
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1
        assert isinstance(run_config.matrix, V1Hyperband)
        assert isinstance(run_config.matrix.params["lr"], V1HpLinSpace)
        assert isinstance(run_config.matrix.params["loss"], V1HpChoice)
        assert run_config.matrix.params["lr"].to_dict() == {
            "kind": "linspace",
            "value": {"start": 0.01, "stop": 0.1, "num": 5},
        }
        assert run_config.matrix.params["loss"].to_dict() == {
            "kind": "choice",
            "value": ["MeanSquaredError", "AbsoluteDifference"],
        }
        assert run_config.matrix.params["normal_rate"].to_dict() == {
            "kind": "normal",
            "value": {"loc": 0, "scale": 0.9},
        }
        assert run_config.matrix.params["dropout"].to_dict() == {
            "kind": "qloguniform",
            "value": {"high": 0.8, "low": 0, "q": 0.1},
        }
        assert run_config.matrix.params["activation"].to_dict() == {
            "kind": "pchoice",
            "value": [["relu", 0.1], ["sigmoid", 0.8]],
        }
        assert run_config.matrix.params["model"].to_dict() == {
            "kind": "choice",
            "value": ["CDNA", "DNA", "STP"],
        }
        assert run_config.matrix.concurrency == 2
        assert isinstance(run_config.matrix, V1Hyperband)
        assert run_config.matrix.kind == V1Hyperband._IDENTIFIER
        assert run_config.matrix.early_stopping is None

        # With build
        plx_file = check_polyaxonfile(
            polyaxonfile=os.path.abspath(
                "tests/fixtures/plain/matrix_job_file_build.yml"
            ),
            is_cli=False,
        )
        run_config = OperationSpecification.compile_operation(plx_file)
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1
        assert run_config.build.hub_ref == "kaniko"
        assert run_config.build.connection == "docker-connection"
        assert run_config.build.params is None
        assert len(run_config.build.run_patch["init"]) == 2
        assert isinstance(run_config.matrix, V1Hyperband)
        assert isinstance(run_config.matrix.params["lr"], V1HpLinSpace)
        assert isinstance(run_config.matrix.params["loss"], V1HpChoice)
        assert run_config.matrix.params["lr"].to_dict() == {
            "kind": "linspace",
            "value": {"start": 0.01, "stop": 0.1, "num": 5},
        }
        assert run_config.matrix.params["loss"].to_dict() == {
            "kind": "choice",
            "value": ["MeanSquaredError", "AbsoluteDifference"],
        }
        assert run_config.matrix.params["normal_rate"].to_dict() == {
            "kind": "normal",
            "value": {"loc": 0, "scale": 0.9},
        }
        assert run_config.matrix.params["dropout"].to_dict() == {
            "kind": "qloguniform",
            "value": {"high": 0.8, "low": 0, "q": 0.1},
        }
        assert run_config.matrix.params["activation"].to_dict() == {
            "kind": "pchoice",
            "value": [["relu", 0.1], ["sigmoid", 0.8]],
        }
        assert run_config.matrix.params["model"].to_dict() == {
            "kind": "choice",
            "value": ["CDNA", "DNA", "STP"],
        }
        assert run_config.matrix.concurrency == 2
        assert isinstance(run_config.matrix, V1Hyperband)
        assert run_config.matrix.kind == V1Hyperband._IDENTIFIER
        assert run_config.matrix.early_stopping is None

    def test_matrix_file_passes_int_float_types(self):
        plx_file = check_polyaxonfile(
            polyaxonfile=os.path.abspath(
                "tests/fixtures/plain/matrix_job_file_with_int_float_types.yml"
            ),
            is_cli=False,
        )
        # Get compiled_operation data
        run_config = OperationSpecification.compile_operation(plx_file)

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1
        assert isinstance(run_config.matrix, V1GridSearch)
        assert isinstance(run_config.matrix.params["param1"], V1HpChoice)
        assert isinstance(run_config.matrix.params["param2"], V1HpChoice)
        assert run_config.matrix.params["param1"].to_dict() == {
            "kind": "choice",
            "value": [1, 2],
        }
        assert run_config.matrix.params["param2"].to_dict() == {
            "kind": "choice",
            "value": [3.3, 4.4],
        }
        assert run_config.matrix.concurrency == 2
        assert isinstance(run_config.matrix, V1GridSearch)
        assert run_config.matrix.kind == V1GridSearch._IDENTIFIER
        assert run_config.matrix.early_stopping is None

    def test_matrix_early_stopping_file_passes(self):
        plx_file = check_polyaxonfile(
            polyaxonfile=os.path.abspath(
                "tests/fixtures/plain/matrix_job_file_early_stopping.yml"
            ),
            is_cli=False,
            to_op=False,
        )
        # Get compiled_operation data
        run_config = OperationSpecification.compile_operation(plx_file)

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1
        assert isinstance(run_config.matrix, V1RandomSearch)
        assert isinstance(run_config.matrix.params["lr"], V1HpLinSpace)
        assert isinstance(run_config.matrix.params["loss"], V1HpChoice)
        assert run_config.matrix.params["lr"].to_dict() == {
            "kind": "linspace",
            "value": {"start": 0.01, "stop": 0.1, "num": 5},
        }
        assert run_config.matrix.params["loss"].to_dict() == {
            "kind": "choice",
            "value": ["MeanSquaredError", "AbsoluteDifference"],
        }
        assert run_config.matrix.concurrency == 2
        assert run_config.matrix.num_runs == 300
        assert isinstance(run_config.matrix, V1RandomSearch)
        assert run_config.matrix.kind == V1RandomSearch._IDENTIFIER
        assert len(run_config.matrix.early_stopping) == 1
        assert isinstance(run_config.matrix.early_stopping[0], V1MetricEarlyStopping)

    def test_mapping_early_stopping_file_passes(self):
        plx_file = check_polyaxonfile(
            polyaxonfile=os.path.abspath(
                "tests/fixtures/plain/mapping_job_file_early_stopping.yml"
            ),
            is_cli=False,
            to_op=False,
        )
        # Get compiled_operation data
        config_run = OperationSpecification.compile_operation(plx_file)

        config_run = CompiledOperationSpecification.apply_operation_contexts(config_run)
        assert config_run.version == 1.1
        assert isinstance(config_run.matrix, V1Mapping)
        assert config_run.matrix.values == [
            {"lr": 0.001, "loss": "MeanSquaredError"},
            {"lr": 0.1, "loss": "AbsoluteDifference"},
        ]
        assert config_run.matrix.concurrency == 2
        assert isinstance(config_run.matrix, V1Mapping)
        assert config_run.matrix.kind == V1Mapping._IDENTIFIER
        assert len(config_run.matrix.early_stopping) == 1
        assert isinstance(config_run.matrix.early_stopping[0], V1MetricEarlyStopping)

    def test_tf_passes(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/plain/distributed_tensorflow_file.yml"),
                {"kind": "compiled_operation"},
            ]
        )

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.build is None
        assert run_config.version == 1.1
        assert run_config.termination is not None
        assert run_config.termination.ttl == 12
        assert run_config.is_tf_job_run
        assert run_config.run.worker.replicas == 5
        assert run_config.run.worker.environment.affinity is not None
        assert run_config.run.worker.environment.restart_policy == "OnFailure"
        assert run_config.run.worker.container.resources == {
            "requests": {"memory": "300Mi"},
            "limits": {"memory": "300Mi"},
        }
        assert run_config.run.ps.replicas == 10
        assert run_config.run.ps.environment.affinity is None
        assert isinstance(run_config.run.ps.environment.tolerations, list)
        assert run_config.run.ps.environment.restart_policy == "OnFailure"
        assert run_config.run.ps.container.resources == {
            "requests": {"cpu": 3, "memory": "256Mi"},
            "limits": {"cpu": 3, "memory": "256Mi"},
        }

        # With build
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath(
                    "tests/fixtures/plain/distributed_tensorflow_file_build.yml"
                ),
                {"kind": "compiled_operation"},
            ]
        )

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.build.hub_ref == "kaniko"
        assert run_config.build.connection == "docker-connection"
        assert len(run_config.build.params) == 1
        assert len(run_config.build.run_patch["init"]) == 2
        assert run_config.version == 1.1
        assert run_config.termination is not None
        assert run_config.termination.ttl == 12
        assert run_config.is_tf_job_run
        assert run_config.run.worker.replicas == 5
        assert run_config.run.worker.environment.affinity is not None
        assert run_config.run.worker.environment.restart_policy == "OnFailure"
        assert run_config.run.worker.container.resources == {
            "requests": {"memory": "300Mi"},
            "limits": {"memory": "300Mi"},
        }
        assert run_config.run.ps.replicas == 10
        assert run_config.run.ps.environment.affinity is None
        assert isinstance(run_config.run.ps.environment.tolerations, list)
        assert run_config.run.ps.environment.restart_policy == "OnFailure"
        assert run_config.run.ps.container.resources == {
            "requests": {"cpu": 3, "memory": "256Mi"},
            "limits": {"cpu": 3, "memory": "256Mi"},
        }

    def test_pytorch_passes(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/plain/distributed_pytorch_file.yml"),
                {"kind": "compiled_operation"},
            ]
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1

        assert run_config.termination is not None
        assert run_config.termination.ttl == 12

        assert run_config.is_pytorch_job_run
        assert run_config.run.master.replicas == 5
        assert run_config.run.master.environment.to_dict() == {
            "restartPolicy": "OnFailure",
            "nodeName": "foo",
            "serviceAccountName": "sa1",
        }
        assert run_config.run.master.container.image == "my_image"
        assert run_config.run.master.container.resources == {
            "requests": {"memory": "300Mi"},
            "limits": {"memory": "300Mi"},
        }
        assert run_config.run.worker.replicas == 10
        assert run_config.run.worker.environment.affinity is None
        assert run_config.run.worker.environment.restart_policy == "OnFailure"
        assert isinstance(run_config.run.worker.environment.tolerations, list)
        assert run_config.run.worker.container.resources == {
            "requests": {"cpu": 3, "memory": "256Mi"},
            "limits": {"cpu": 3, "memory": "256Mi"},
        }

    def test_mpi_passes(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/plain/distributed_mpi_file.yml"),
                {"kind": "compiled_operation"},
            ]
        )

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.version == 1.1
        assert run_config.is_mpi_job_run
        assert run_config.termination is None
        assert run_config.run.launcher.replicas == 1
        assert run_config.run.launcher.to_dict() == {
            "replicas": 1,
            "container": {
                "image": "mpioperator/tensorflow-benchmarks:latest",
                "command": ["mpirun", "python", "run.py"],
            },
        }
        assert run_config.run.launcher.environment is None

        assert run_config.run.worker.replicas == 2
        assert run_config.run.worker.environment.affinity is None
        assert run_config.run.worker.environment.node_selector is not None
        assert isinstance(run_config.run.worker.environment.tolerations, list)
        assert run_config.run.worker.to_dict()["container"] == {
            "image": "mpioperator/tensorflow-benchmarks:latest",
            "command": ["mpirun", "python", "run.py"],
            "resources": {"limits": {"nvidia.com/gpu": 1}},
        }

    def test_ray_passes(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/plain/distributed_ray_file.yml"),
                {"kind": "compiled_operation"},
            ]
        )

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.build is None
        assert run_config.version == 1.1
        assert run_config.termination is not None
        assert run_config.termination.ttl == 12
        assert run_config.is_ray_job_run
        assert run_config.run.workers["small-group"].replicas == 5
        assert run_config.run.workers["small-group"].min_replicas == 5
        assert run_config.run.workers["small-group"].max_replicas == 15
        assert run_config.run.workers["small-group"].environment.affinity is not None
        assert (
            run_config.run.workers["small-group"].environment.restart_policy
            == "OnFailure"
        )
        assert run_config.run.workers["small-group"].container.resources == {
            "limits": {"cpu": "1"},
            "requests": {"cpu": "200m"},
        }
        assert run_config.run.head.replicas is None
        assert run_config.run.head.environment.affinity is None
        assert isinstance(run_config.run.head.environment.tolerations, list)
        assert run_config.run.head.environment.restart_policy == "OnFailure"
        assert run_config.run.head.container.resources == {
            "limits": {"cpu": "1"},
            "requests": {"cpu": "200m"},
        }

    def test_dask_passes(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/plain/distributed_dask_file.yml"),
                {"kind": "compiled_operation"},
            ]
        )

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.build is None
        assert run_config.version == 1.1
        assert run_config.termination is not None
        assert run_config.termination.ttl == 12
        assert run_config.is_dask_job_run
        assert run_config.run.worker.replicas == 5
        assert run_config.run.worker.environment.restart_policy == "OnFailure"
        assert run_config.run.worker.container.resources == {
            "limits": {"cpu": "1"},
            "requests": {"cpu": "200m"},
        }
        assert run_config.run.job.replicas is None
        assert run_config.run.job.environment.affinity is None
        assert isinstance(run_config.run.job.environment.tolerations, list)
        assert run_config.run.job.environment.restart_policy == "OnFailure"
        assert run_config.run.job.container.resources == {
            "limits": {"cpu": "1"},
            "requests": {"cpu": "200m"},
        }
        assert run_config.run.scheduler.replicas is None
        assert run_config.run.scheduler.environment.affinity is None
        assert isinstance(run_config.run.scheduler.environment.tolerations, list)
        assert run_config.run.scheduler.environment.restart_policy == "OnFailure"
        assert run_config.run.scheduler.container.resources == {
            "limits": {"cpu": "1"},
            "requests": {"cpu": "200m"},
        }

    def test_specification_with_quotes(self):
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath("tests/fixtures/plain/polyaxonfile_with_quotes.yaml"),
                {"kind": "compiled_operation"},
            ]
        )

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        expected_run = {
            "kind": V1RunKind.JOB,
            "container": {
                "image": "continuumio/miniconda3",
                "command": ["python"],
                "args": ["-c \"print('Tweet tweet')\""],
            },
        }
        assert run_config.run.to_dict() == expected_run
        run_config = V1CompiledOperation.read(run_config.to_dict())
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.run.to_dict() == expected_run

    def test_specification_with_context_requirement(self):
        context_root = ctx_paths.CONTEXT_ROOT
        contexts = {
            "globals": {
                "owner_name": "user",
                "project_name": "project",
                "project_unique_name": "user.project",
                "project_uuid": "uuid",
                "run_info": "user.project.runs.uuid",
                "name": "run",
                "uuid": "uuid",
                "context_path": "/plx-context",
                "artifacts_path": "{}/artifacts".format(context_root),
                "run_artifacts_path": "{}/artifacts/test".format(context_root),
                "run_outputs_path": "{}/artifacts/test/outputs".format(context_root),
                "namespace": "test",
                "iteration": 12,
                "ports": [1212, 1234],
                "base_url": "/services/v1/test/user/project/runs/uuid/80",
                "base_urls": ["/services/v1/test/user/project/runs/uuid/80"],
                "created_at": None,
                "compiled_at": None,
                "cloning_kind": None,
                "original_uuid": None,
            },
            "init": {},
            "connections": {"foo": {"key": "connection-value"}},
        }
        run_config = CompiledOperationSpecification.read(
            [
                os.path.abspath(
                    "tests/fixtures/plain/polyaxonfile_with_contexts_requirements.yaml"
                ),
                {"kind": "compiled_operation"},
            ]
        )

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        expected_run = {
            "kind": V1RunKind.JOB,
            "init": [
                {
                    "artifacts": {"files": ["{{globals.run_outputs_path}}/foo"]},
                    "connection": "{{connections['foo']['key']}}",
                }
            ],
            "container": {
                "image": "continuumio/miniconda3",
                "command": ["python"],
                "workingDir": "{{ globals.artifacts_path }}/repo",
                "args": ["-c \"print('Tweet tweet')\""],
            },
        }
        assert run_config.run.to_dict() == expected_run
        run_config = V1CompiledOperation.read(run_config.to_dict())
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        assert run_config.run.to_dict() == expected_run

        expected_run = {
            "kind": V1RunKind.JOB,
            "init": [
                {
                    "artifacts": {
                        "files": [
                            "{}/artifacts/test/outputs/foo".format(
                                ctx_paths.CONTEXT_ROOT
                            )
                        ],
                    },
                    "connection": "connection-value",
                }
            ],
            "container": {
                "image": "continuumio/miniconda3",
                "command": ["python"],
                "workingDir": "{}/artifacts/repo".format(ctx_paths.CONTEXT_ROOT),
                "args": ["-c \"print('Tweet tweet')\""],
            },
        }
        run_config = CompiledOperationSpecification.apply_runtime_contexts(
            run_config, contexts=contexts
        )
        assert run_config.run.to_dict() == expected_run
