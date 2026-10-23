from datetime import timedelta
from mock import MagicMock, patch
import os
from pathlib import Path
import pytest
import tempfile

from polyaxon import pkg
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import ENV_KEYS_USE_GIT_REGISTRY
from polyaxon._flow.early_stopping.policies import V1MetricEarlyStopping
from polyaxon._flow.environment import V1Environment
from polyaxon._flow.matrix.grid_search import V1GridSearch
from polyaxon._flow.matrix.hyperband import V1Hyperband
from polyaxon._flow.matrix.mapping import V1Mapping
from polyaxon._flow.matrix.params import V1HpChoice, V1HpLinSpace
from polyaxon._flow.matrix.random_search import V1RandomSearch
from polyaxon._flow.operations.compiled_operation import V1CompiledOperation
from polyaxon._flow.plugins import V1Plugins
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.termination import V1Termination
from polyaxon._polyaxonfile import check_polyaxonfile, get_op_specification
from polyaxon._polyaxonfile.params import parse_params
from polyaxon._polyaxonfile.specs import (
    CompiledOperationSpecification,
    OperationSpecification,
)
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonfileError, PolyaxonValidationError
from polyaxon.schemas import V1ProjectVersionKind


@pytest.mark.polyaxonfile_mark
class TestPolyaxonfiles(BaseTestCase):
    def test_missing_version_passes(self):
        operation = check_polyaxonfile(
            polyaxonfile=os.path.abspath("tests/fixtures/plain/missing_version.yml"),
            is_cli=False,
        )

        assert operation.version is None
        assert operation.component.version is None

    @patch("polyaxon._polyaxonfile.check.Printer.warning")
    def test_version_is_ignored(self, warning):
        operation = check_polyaxonfile(
            polyaxonfile=os.path.abspath("tests/fixtures/plain/non_supported_file.yml"),
            is_cli=False,
        )

        assert operation.version == 0.4
        assert operation.component.version == 0.4
        warning.assert_not_called()

    @patch("polyaxon._polyaxonfile.check.Printer.warning")
    def test_cli_warns_for_supplied_version(self, warning):
        check_polyaxonfile(
            polyaxonfile=os.path.abspath("tests/fixtures/plain/non_supported_file.yml"),
            is_cli=True,
        )

        warning.assert_called_once_with(
            "Polyaxonfile `version` is no longer required. It is retained "
            "for compatibility but ignored by validation."
        )

    def test_non_existing_raises(self):
        with self.assertRaises(PolyaxonfileError):
            check_polyaxonfile(
                polyaxonfile=os.path.abspath(
                    "tests/fixtures/plain/non_existing_file.yml"
                ),
                is_cli=False,
            )

    def test_file_without_kind_or_runtime_raises(self):
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

    def test_sandbox_requires_an_operation(self):
        with self.assertRaises(PolyaxonfileError):
            check_polyaxonfile(
                polyaxonfile=os.path.abspath("tests/fixtures/plain/simple_job.yml"),
                sandbox=True,
                is_cli=False,
                to_op=False,
            )

    def test_sandbox_checks_do_not_depend_on_param_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            job = Path(directory) / "job.yaml"
            job.write_text("run: {kind: job, container: {image: base:v1}}\n")
            matrix = Path(directory) / "matrix.yaml"
            matrix.write_text(
                "inputs: [{name: lr, type: float, isOptional: true, value: 0.1}]\n"
                "matrix: {kind: grid, params: {lr: {kind: choice, value: [0.1, 0.2]}}}\n"
                "run: {kind: service, container: {image: base:v1}}\n"
            )
            for source, message in (
                (job, "only supported on kind: service"),
                (matrix, "do not support matrix"),
            ):
                with self.subTest(source=source.name):
                    with self.assertRaises(PolyaxonfileError) as error:
                        check_polyaxonfile(
                            polyaxonfile=str(source),
                            sandbox=True,
                            validate_params=False,
                            is_cli=False,
                        )
                    assert message in str(error.exception.__cause__)

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
        with patch(
            "polyaxon._sdk.api.projects_v1_api.ProjectsV1Api.get_version"
        ) as request_mock:
            request_mock.return_value = MagicMock(
                kind=V1ProjectVersionKind.COMPONENT,
                content=os.path.abspath("tests/fixtures/plain/simple_job.yml"),
            )
            operation = check_polyaxonfile(hub="component:12", is_cli=False, to_op=True)

        assert request_mock.call_count == 1
        assert operation.kind == "operation"
        assert operation.hub_ref == "component:12"
        assert operation.component.run.container.image == "python-with-boto3"

    @patch("polyaxon._config.spec.ConfigSpec.read_from_url")
    def test_operation_file_resolves_url_ref(self, read_from_url):
        read_from_url.return_value = {
            "kind": "component",
            "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
        }
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "run.yml"
            source.write_text("kind: operation\nurlRef: https://example.com/job.yml\n")
            operation = check_polyaxonfile(polyaxonfile=str(source), is_cli=False)

        read_from_url.assert_called_once_with("https://example.com/job.yml")
        assert operation.url_ref == "https://example.com/job.yml"
        assert operation.component.run.container.image == "busybox:1.36"

    def test_from_hub(self):
        with patch(
            "polyaxon._sdk.api.projects_v1_api.ProjectsV1Api.get_version"
        ) as request_mock:
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

    def test_passing_params_to_no_io_overrides_polyaxonfiles(self):
        op_config = check_polyaxonfile(
            polyaxonfile=os.path.abspath("tests/fixtures/plain/simple_job.yml"),
            params={"flag": True, "loss": "some-loss"},
            is_cli=False,
        )
        assert op_config.params["flag"].value is True
        assert op_config.params["loss"].value == "some-loss"
        assert "strictParams" not in op_config.to_dict()

        op_config = check_polyaxonfile(
            polyaxonfile=os.path.abspath("tests/fixtures/plain/simple_job.yml"),
            params={"flag": True, "loss": "some-loss"},
            strict_params=False,
            is_cli=False,
        )
        assert op_config.to_dict()["strictParams"] is False

        with self.assertRaises(PolyaxonfileError) as error:
            check_polyaxonfile(
                polyaxonfile=os.path.abspath("tests/fixtures/plain/simple_job.yml"),
                params={"flag": True, "loss": "some-loss"},
                strict_params=True,
                is_cli=False,
            )
        assert isinstance(error.exception.__cause__, PolyaxonValidationError)
        assert "undeclared param" in str(error.exception.__cause__)

    def test_strict_params_flag_beats_preset(self):
        for strict_params, expected in ((None, True), (False, False)):
            op_config = check_polyaxonfile(
                polyaxonfile=[
                    os.path.abspath("tests/fixtures/plain/simple_job.yml"),
                    os.path.abspath("tests/fixtures/plain/strict_params_preset.yml"),
                ],
                strict_params=strict_params,
                is_cli=False,
            )
            assert op_config.strict_params is expected

        with self.assertRaises(PolyaxonfileError) as error:
            check_polyaxonfile(
                polyaxonfile=[
                    os.path.abspath("tests/fixtures/plain/simple_job.yml"),
                    os.path.abspath("tests/fixtures/plain/strict_params_preset.yml"),
                ],
                params={"flag": True, "loss": "some-loss"},
                is_cli=False,
            )
        assert isinstance(error.exception.__cause__, PolyaxonValidationError)
        assert "undeclared param" in str(error.exception.__cause__)

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

    def test_passing_short_params_overrides_polyaxonfiles(self):
        # Test that short form params (without the "value" wrapper) are parsed correctly
        op_config = OperationSpecification.read(
            [
                os.path.abspath(
                    "tests/fixtures/typing/required_inputs_with_short_params.yml"
                ),
            ]
        )

        # Verify params are parsed correctly from short form
        assert op_config.params["loss"].value == "MeanSquaredError"
        assert op_config.params["flag"].value is True

        # Compile the operation and apply params
        run_config = OperationSpecification.compile_operation(op_config)
        # Apply the params from the operation to the compiled operation
        run_config.apply_params(params=op_config.params)
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        run_config = CompiledOperationSpecification.apply_runtime_contexts(run_config)
        assert run_config.version == 1.1
        assert run_config.tags == ["foo", "bar"]
        assert run_config.run.container.image == "my_image"
        assert run_config.run.container.command == ["/bin/sh", "-c"]
        assert (
            run_config.run.container.args
            == "video_prediction_train --loss=MeanSquaredError --flag"
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
        assert run_config.is_ray_cluster_run
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

    def test_ray_start_params_keep_strings_after_runtime_contexts(self):
        run_config = V1CompiledOperation.read(
            {
                "version": 1.1,
                "kind": "compiled_operation",
                "run": {
                    "kind": "raycluster",
                    "head": {
                        "rayStartParams": {
                            "num-cpus": "0",
                            "dashboard-host": "0.0.0.0",
                        },
                        "container": {"image": "rayproject/ray:2.46.0"},
                    },
                    "workers": {
                        "small": {
                            "rayStartParams": {"num-cpus": "1"},
                            "container": {"image": "rayproject/ray:2.46.0"},
                        }
                    },
                },
            }
        )

        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        run_config = CompiledOperationSpecification.apply_runtime_contexts(
            run_config,
            contexts={
                "head": {"globals": {"uuid": "uuid"}},
                "workers": {"small": {"globals": {"uuid": "uuid"}}},
            },
        )
        assert run_config.run.head.ray_start_params == {
            "num-cpus": "0",
            "dashboard-host": "0.0.0.0",
        }
        assert run_config.run.workers["small"].ray_start_params == {"num-cpus": "1"}

    def test_container_command_args_keep_literal_text_after_runtime_contexts(self):
        values = [
            "0",
            "False",
            "0.0",
            "[]",
            '{"lr": 0.1}',
            "1e3",
            "+1",
            "0x10",
            '"v1"',
            "1",
            "2.5",
            "True",
            "plain",
        ]
        container = {"image": "test", "command": values, "args": values}
        run_config = V1CompiledOperation.read(
            {
                "kind": "compiled_operation",
                "run": {
                    "kind": "job",
                    "container": container,
                    "sidecars": [container],
                    "init": [{"container": container}],
                },
            }
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        parsed = CompiledOperationSpecification.apply_runtime_contexts(run_config)

        for parsed_container in (
            parsed.run.container,
            parsed.run.sidecars[0],
            parsed.run.init[0].container,
        ):
            assert parsed_container.command == values
            assert parsed_container.args == values

    def test_container_command_args_keep_falsy_template_text(self):
        values = [
            "{{ seed }}",
            "{{ dropout }}",
            "{{ verbose }}",
            "{{ ckpt }}",
            "{{ empty }}",
            "None",
            "{% raw %}{{ ds }}{% endraw %}",
        ]
        run_config = V1CompiledOperation.read(
            {
                "kind": "compiled_operation",
                "run": {
                    "kind": "job",
                    "container": {
                        "image": "test",
                        "command": values,
                        "args": values,
                    },
                },
            }
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        run_config = CompiledOperationSpecification.apply_runtime_contexts(
            run_config,
            contexts={
                "seed": 0,
                "dropout": 0.0,
                "verbose": False,
                "ckpt": None,
                "empty": "",
            },
        )

        expected = ["0", "0.0", "False", None, "", "None", "{{ ds }}"]
        assert run_config.run.container.command == expected
        assert run_config.run.container.args == expected

    def test_container_args_keep_non_string_expression_parsing(self):
        run_config = V1CompiledOperation.read(
            {
                "kind": "compiled_operation",
                "run": {
                    "kind": "job",
                    "container": {
                        "image": "test",
                        "args": [0, 0.0, False],
                    },
                },
            }
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        run_config = CompiledOperationSpecification.apply_runtime_contexts(run_config)

        assert run_config.run.container.args == [0, 0.0, False]
        assert [type(value) for value in run_config.run.container.args] == [
            int,
            float,
            bool,
        ]

    def test_ray_container_args_follow_worker_names_and_replica_contexts(self):
        worker_names = ["container", "sidecars", "{{ group }}"]
        replica = {"container": {"image": "test", "args": ["{{ value }}", "1e3"]}}
        run_config = V1CompiledOperation.read(
            {
                "kind": "compiled_operation",
                "run": {
                    "kind": "raycluster",
                    "head": replica,
                    "workers": {name: replica for name in worker_names},
                },
            }
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        run_config = CompiledOperationSpecification.apply_runtime_contexts(
            run_config,
            contexts={
                "head": {"value": 0},
                "workers": {"value": False, "group": "gpu"},
            },
        )

        assert run_config.run.head.container.args == ["0", "1e3"]
        assert set(run_config.run.workers) == {"container", "sidecars", "gpu"}
        for worker in run_config.run.workers.values():
            assert worker.container.args == ["False", "1e3"]

    def test_tf_container_args_skip_replicas_without_contexts(self):
        replica = {"container": {"image": "test", "args": ["{{ value }}", "1e3"]}}
        run_config = V1CompiledOperation.read(
            {
                "kind": "compiled_operation",
                "run": {
                    "kind": "tfjob",
                    "chief": replica,
                    "worker": replica,
                },
            }
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        run_config = CompiledOperationSpecification.apply_runtime_contexts(
            run_config, contexts={"worker": {"value": 0}}
        )

        assert run_config.run.worker.container.args == ["0", "1e3"]
        assert run_config.run.chief.container.args == ["{{ value }}", "1e3"]

    def test_container_text_preservation_does_not_change_initializer_data(self):
        run_config = V1CompiledOperation.read(
            {
                "kind": "compiled_operation",
                "run": {
                    "kind": "job",
                    "container": {"image": "test", "args": ["{{ value }}"]},
                    "init": [
                        {
                            "dockerfile": {
                                "image": "test",
                                "env": {"container": {"args": ["{{ value }}"]}},
                            }
                        }
                    ],
                },
            }
        )
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        run_config = CompiledOperationSpecification.apply_runtime_contexts(
            run_config, contexts={"value": 0}
        )

        assert run_config.run.container.args == ["0"]
        assert run_config.run.init[0].dockerfile.env == {"container": {"args": [0]}}

    def test_runtime_contexts_without_run(self):
        run_config = V1CompiledOperation.read({"kind": "compiled_operation"})

        run_config = CompiledOperationSpecification.apply_runtime_contexts(run_config)

        assert run_config.run is None

    def _compile_input_values(self, inputs, params, contexts=None):
        run_config = V1CompiledOperation.read(
            {
                "kind": "compiled_operation",
                "inputs": inputs,
                "run": {"kind": "job", "container": {"image": "test"}},
            }
        )
        run_config.apply_params(params=params)
        run_config = CompiledOperationSpecification.apply_operation_contexts(
            run_config, contexts=contexts
        )
        return {io.name: io.value for io in run_config.inputs}

    def test_typed_str_input_values_keep_text(self):
        values = {
            "zero": "0",
            "exp": "1e3",
            "json": '{"lr": 0.1}',
            "quoted": '"v1"',
            "none": "None",
            "escaped": "{% raw %}{{ ds }}{% endraw %}",
        }
        result = self._compile_input_values(
            [{"name": name, "type": "str"} for name in values],
            {name: {"value": value} for name, value in values.items()},
        )

        assert result == {**values, "escaped": "{{ ds }}"}

    def test_typed_str_input_values_match_str_options(self):
        raw = "{% raw %}{{ ds }}{% endraw %}"
        for value, options, expected in (
            ("0", ["0", "1"], "0"),
            (raw, [raw], "{{ ds }}"),
        ):
            with self.subTest(value=value):
                result = self._compile_input_values(
                    [{"name": "x", "type": "str", "options": options}],
                    {"x": {"value": value}},
                )

                assert result == {"x": expected}

    def test_text_list_input_values_keep_item_text(self):
        for io, value in (
            ({"name": "x", "type": "List[str]"}, ["--a", "1", "--b", "0"]),
            ({"name": "x", "type": "List[str]", "options": ["0", "1"]}, ["0", "1"]),
            (
                {"name": "x", "type": "str", "isList": True, "options": ["0", "1"]},
                ["0", "1"],
            ),
        ):
            with self.subTest(io=io):
                result = self._compile_input_values([io], {"x": {"value": value}})

                assert result == {"x": value}

    def test_text_list_input_serialized_default_is_read_as_a_list(self):
        result = self._compile_input_values(
            [{"name": "x", "type": "List[str]", "value": '["0"]'}], {}
        )

        assert result == {"x": ["0"]}

    def test_typed_str_input_values_render_contexts(self):
        for value, uuid, expected in (
            ("{{ globals.uuid }}", "abc123", "abc123"),
            ("{{ globals.uuid }}", None, "None"),
            ("{{ 'None' }}", "abc123", "None"),
        ):
            with self.subTest(value=value, uuid=uuid):
                result = self._compile_input_values(
                    [{"name": "x", "type": "str"}],
                    {"x": {"value": value}},
                    contexts={"globals": {"uuid": uuid}},
                )

                assert result == {"x": expected}

    def test_typed_str_param_keeps_text_in_container_args(self):
        run_config = V1CompiledOperation.read(
            {
                "kind": "compiled_operation",
                "inputs": [{"name": "n", "type": "str"}],
                "run": {
                    "kind": "job",
                    "container": {"image": "test", "args": ["--n", "{{ n }}"]},
                },
            }
        )
        run_config.apply_params(params={"n": {"value": "1e3"}})
        run_config = CompiledOperationSpecification.apply_operation_contexts(run_config)
        run_config = CompiledOperationSpecification.apply_runtime_contexts(run_config)

        assert run_config.run.container.args == ["--n", "1e3"]

    def test_non_text_input_values_keep_literal_conversion(self):
        result = self._compile_input_values(
            [
                {"name": "untyped"},
                {"name": "flag", "type": "any"},
                {"name": "lr", "type": "float", "value": "0.1"},
                {"name": "ids", "type": "list", "value": ["0"]},
            ],
            {"untyped": {"value": "0"}, "flag": {"value": "{{ 1 == 2 }}"}},
        )

        assert result == {"untyped": 0, "flag": False, "lr": 0.1, "ids": [0]}

    def test_non_text_output_templated_options_keep_literal_conversion(self):
        templated = ["{{ globals.allowed }}"]
        for io, allowed, expected in (
            ({"type": "int", "options": templated}, 1, [1]),
            ({"type": "int", "options": "{{ globals.allowed }}"}, [1, 2], [1, 2]),
            ({"type": "int", "options": "{{ globals.allowed }}"}, None, None),
            # isList with List[str] declares nested lists, not a text declaration
            (
                {"type": "List[str]", "isList": True, "options": templated},
                ["0"],
                [["0"]],
            ),
        ):
            with self.subTest(io=io, allowed=allowed):
                run_config = V1CompiledOperation.read(
                    {
                        "kind": "compiled_operation",
                        "outputs": [{"name": "out", **io}],
                        "run": {"kind": "job", "container": {"image": "test"}},
                    }
                )
                run_config = CompiledOperationSpecification.apply_operation_contexts(
                    run_config, contexts={"globals": {"allowed": allowed}}
                )

                assert run_config.outputs[0].validation.options == expected

    def _check_sdk_params(self, content, params, preset=None, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            polyaxonfile = Path(directory) / "polyaxonfile.yaml"
            polyaxonfile.write_text(content)
            files = [str(polyaxonfile)]
            if preset:
                preset_file = Path(directory) / "preset.yaml"
                preset_file.write_text(preset)
                files.append(str(preset_file))
            return check_polyaxonfile(
                polyaxonfile=files, params=params, is_cli=False, **kwargs
            )

    @staticmethod
    def _compile_op(op_config):
        run_config = OperationSpecification.compile_operation(op_config)
        run_config.apply_params(params=op_config.params)
        return CompiledOperationSpecification.apply_operation_contexts(run_config)

    def test_sdk_params_keep_typed_str_text(self):
        job = "run: {kind: job, container: {image: base:v1}}\n"
        for content, value in (
            ("inputs: [{name: n, type: str}]\n" + job, '{"lr": 0.1}'),
            (
                "kind: operation\n"
                "component:\n"
                "  inputs: [{name: n, type: str}]\n"
                "  run: {kind: job, container: {image: base:v1}}\n",
                "1e3",
            ),
            ("outputs: [{name: n, type: str}]\n" + job, "0"),
        ):
            with self.subTest(content=content):
                op_config = self._check_sdk_params(content, {"n": value})
                run_config = self._compile_op(op_config)
                ios = (run_config.inputs or []) + (run_config.outputs or [])

                assert op_config.params["n"].value == value
                assert ios[0].value == value

    def test_sdk_params_are_sent_as_given(self):
        params = {
            "zero": "0",
            "nested": {"k": "0"},
            "pair": ("0", "1"),
            "key": {"1": 2},
            "duration": timedelta(seconds=5),
            "enum": V1RunKind.JOB,
        }
        op_config = self._check_sdk_params(
            "run: {kind: job, container: {image: base:v1}}\n", params
        )
        values = {name: param.value for name, param in op_config.params.items()}

        assert values == {**params, "duration": 5.0, "enum": "job"}
        assert type(values["pair"]) is tuple
        assert type(values["enum"]) is str

        op_config = get_op_specification(
            hub="component:1.0",
            params=parse_params({"n": "0"}, is_cli=False),
            validate_params=False,
        )

        assert op_config.params["n"].value == "0"

    def test_sdk_typed_params_convert_at_compile(self):
        op_config = self._check_sdk_params(
            "inputs: [{name: n, type: int}]\n"
            "run: {kind: job, container: {image: base:v1}}\n",
            {"n": "0"},
        )
        run_config = self._compile_op(op_config)

        assert op_config.params["n"].value == "0"
        assert run_config.inputs[0].value == 0

    def test_sdk_params_merge_with_yaml_params(self):
        content = (
            "params: {cfg: {value: {yaml: '1'}}}\n"
            "run: {kind: job, container: {image: base:v1}}\n"
        )
        for value, expected in (
            ({"sdk": "0"}, {"yaml": "1", "sdk": "0"}),
            ('{"sdk": "0"}', '{"sdk": "0"}'),
        ):
            with self.subTest(value=value):
                op_config = self._check_sdk_params(content, {"cfg": value})

                assert op_config.params["cfg"].value == expected

    def test_sdk_params_beat_preset(self):
        op_config = self._check_sdk_params(
            "run: {kind: job, container: {image: base:v1}}\n",
            {"n": "0"},
            preset="isPreset: true\nparams: {n: {value: '5'}}\n",
        )

        assert op_config.params["n"].value == "0"

    def test_flags_beat_file_overlays(self):
        job = "run: {kind: job, container: {image: base:v1}}\n"
        preset = (
            "isPreset: true\n"
            "queue: gpu-a\n"
            "presets: [team]\n"
            "params: {lr: {value: '0.01', contextOnly: true}}\n"
        )
        for kind in (None, "operation", "component"):
            with self.subTest(kind=kind):
                op_config = self._check_sdk_params(
                    f"kind: {kind}\n{job}" if kind else job,
                    ["lr=0.1"],
                    preset=preset,
                    queue="gpu-b",
                    presets=["cli"],
                )

                assert op_config.queue == "gpu-b"
                assert op_config.presets == ["cli"]
                assert op_config.params["lr"].value == "0.1"
                assert op_config.params["lr"].context_only is True

    def test_matrix_flag_of_other_kind_replaces_file_matrix(self):
        job = (
            "inputs: [{name: x, type: int, value: 0, isOptional: true}]\n"
            "run: {kind: job, container: {image: base:v1}}\n"
        )
        matrix = "matrix: {kind: mapping, values: [{x: 1}]}\n"
        for content, preset in (
            (matrix + job, None),
            (job, "isPreset: true\n" + matrix),
        ):
            with self.subTest(preset=preset):
                op_config = self._check_sdk_params(
                    content,
                    None,
                    preset=preset,
                    hparams={"x": {"kind": "choice", "value": [1, 2]}},
                )

                assert op_config.matrix.kind == "grid"
                assert "values" not in op_config.matrix.to_dict()

    def test_partial_matrix_flag_merges_file_matrix(self):
        job = (
            "inputs: [{name: x, type: int, value: 0, isOptional: true}]\n"
            "run: {kind: job, container: {image: base:v1}}\n"
        )
        matrix = "matrix: {kind: grid, params: {x: {kind: choice, value: [1, 2]}}}\n"
        for content, preset in (
            (matrix + job, None),
            (job, "isPreset: true\n" + matrix),
        ):
            with self.subTest(preset=preset):
                op_config = self._check_sdk_params(
                    content, None, preset=preset, matrix={"concurrency": 4}
                )

                assert op_config.matrix.kind == "grid"
                assert op_config.matrix.concurrency == 4
                assert set(op_config.matrix.params) == {"x"}

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
        assert run_config.is_dask_cluster_run
        assert run_config.run.worker.replicas == 5
        assert run_config.run.worker.environment.restart_policy == "OnFailure"
        assert run_config.run.worker.container.resources == {
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
