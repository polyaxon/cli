from copy import deepcopy
import pytest

from clipped.compact.pydantic import ValidationError
from polyaxon import schemas
from polyaxon._flow.component.component import V1Component
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._polyaxonfile.specs.component import ComponentSpecification
from polyaxon._polyaxonfile.specs.operation import OperationSpecification
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.components_mark
class TestPolyaxonfile(BaseTestCase):
    def test_existing_field_union_and_export(self):
        assert schemas.V1Polyaxonfile is V1Polyaxonfile

        aliases = V1Polyaxonfile.get_aliases()
        for model in (V1Component, V1Operation):
            assert issubclass(model, V1Polyaxonfile)
            assert set(model.get_model_fields()) == set(
                V1Polyaxonfile.get_model_fields()
            )
            for name, alias in model.get_aliases().items():
                assert aliases[name] == alias

    def test_combined_fields_do_not_depend_on_kind(self):
        source = {
            "inputs": [{"name": "count", "type": "int"}],
            "outputs": [{"name": "result", "type": "str"}],
            "params": {"count": {"value": 3}},
            "matrix": {
                "kind": "grid",
                "params": {"seed": {"kind": "choice", "value": [1, 2]}},
            },
            "schedule": {"kind": "cron", "cron": "0 * * * *"},
            "strictParams": False,
            "template": {"enabled": False},
            "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
        }
        for kind in (None, "component", "operation"):
            with self.subTest(kind=kind):
                authored = {**source, "kind": kind} if kind else deepcopy(source)
                config = V1Polyaxonfile.from_dict(authored)

                assert config.kind == kind
                assert config.inputs[0].name == "count"
                assert config.outputs[0].name == "result"
                assert config.params["count"].value == 3
                assert isinstance(config.matrix, schemas.V1GridSearch)
                assert isinstance(config.schedule, schemas.V1CronSchedule)
                assert isinstance(config.run, schemas.V1Job)
                assert config.strict_params is False
                assert config.is_template() is False
                assert config.to_dict() == authored
                assert V1Polyaxonfile.read(config.to_json()).to_dict() == authored

    def test_param_normalization_matches_operation(self):
        params = {
            "count": 3,
            "enabled": False,
            "names": ["a", "b"],
            "options": {"optimizer": "adam"},
            "unset": None,
            "empty": {},
            "message": {"value": "hello", "contextOnly": True, "toEnv": "MESSAGE"},
            "result": {"ref": "ops.train", "value": "outputs.result"},
        }
        source = {"hubRef": "train:v1", "params": params}
        config = V1Polyaxonfile.from_dict(source)
        legacy = V1Operation.from_dict(source)

        assert config.to_dict() == legacy.to_dict()
        assert config.params["unset"].value is None
        assert "value" in config.params["unset"].model_fields_set
        assert "value" not in config.params["empty"].model_fields_set
        assert config.params["message"].context_only is True
        assert config.params["message"].to_env == "MESSAGE"
        assert config.params["result"].ref == "ops.train"

    def test_preserves_root_field_presence(self):
        omitted = V1Polyaxonfile.from_dict({"hubRef": "train:v1"})
        assert omitted.kind is None
        assert omitted.version is None
        assert omitted.strict_params is None
        assert omitted.model_fields_set == {"hub_ref"}
        assert omitted.to_dict() == {"hubRef": "train:v1"}

        source = {
            "kind": None,
            "version": None,
            "queue": None,
            "strictParams": False,
            "isApproved": False,
            "presets": [],
            "inputs": [],
            "params": {},
            "hubRef": "train:v1",
        }
        config = V1Polyaxonfile.from_dict(source)
        assert config.to_dict(exclude_none=False) == source
        assert config.to_dict() == {
            key: value for key, value in source.items() if value is not None
        }
        assert (
            V1Polyaxonfile.from_dict(
                config.to_dict(exclude_none=False)
            ).model_fields_set
            == config.model_fields_set
        )

        for strict_params in (None, False, True):
            config = V1Polyaxonfile.from_dict({"strictParams": strict_params})
            assert config.strict_params is strict_params
            assert "strict_params" in config.model_fields_set

    def test_python_field_names_use_existing_json_aliases(self):
        config = V1Polyaxonfile(
            hub_ref="train:v1",
            strict_params=False,
            patch_strategy=schemas.V1PatchStrategy.PRE_MERGE,
            is_preset=True,
            run_patch={"container": {"image": "custom:v2"}},
            skip_on_upstream_skip=False,
        )
        assert config.to_dict() == {
            "hubRef": "train:v1",
            "strictParams": False,
            "patchStrategy": "pre_merge",
            "isPreset": True,
            "runPatch": {"container": {"image": "custom:v2"}},
            "skipOnUpstreamSkip": False,
        }

    def test_reference_and_embedded_component_are_preserved_without_merging(self):
        for field, value in (
            ("hubRef", "train:v1"),
            ("dagRef", "train"),
            ("pathRef", "./train.yaml"),
            ("urlRef", "https://example.com/train.yaml"),
        ):
            with self.subTest(reference=field):
                source = {
                    field: value,
                    "component": {
                        "params": {"count": {"value": 1}},
                        "run": {"kind": "job", "container": {"image": "base:v1"}},
                    },
                    "params": {"count": {"value": 3}},
                    "run": {"kind": "job", "container": {"image": "local:v2"}},
                    "runPatch": {"container": {"image": "final:v3"}},
                }
                original = deepcopy(source)
                config = V1Polyaxonfile.from_dict(source)

                assert isinstance(config.component, V1Polyaxonfile)
                assert config.component.params["count"].value == 1
                assert config.params["count"].value == 3
                assert config.component.run.container.image == "base:v1"
                assert config.run.container.image == "local:v2"
                assert config.to_dict() == original
                assert source == original

    def test_recursive_components_accept_shared_fields(self):
        source = {
            "params": {"count": {"value": 3}},
            "component": {
                "strictParams": False,
                "queue": None,
                "component": {
                    "hubRef": "base:v1",
                    "inputs": [{"name": "count", "type": "int"}],
                    "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
                },
            },
        }
        config = V1Polyaxonfile.from_dict(source)

        assert isinstance(config.component, V1Polyaxonfile)
        assert isinstance(config.component.component, V1Polyaxonfile)
        assert config.component.component.inputs[0].name == "count"
        assert config.component.component.hub_ref == "base:v1"
        assert config.component.queue is None
        assert "queue" in config.component.model_fields_set
        assert "queue" not in config.component.component.model_fields_set
        assert config.component.strict_params is False

    def test_incomplete_authoring_layers_keep_typed_fields(self):
        for source in (
            {},
            {"params": {"count": {"value": 3}}},
            {"hubRef": "train:v1"},
            {"isPreset": True, "queue": "gpu"},
            {"component": {"params": {"count": {"value": 3}}}},
            {"run": {"kind": "job"}},
        ):
            with self.subTest(source=source):
                assert V1Polyaxonfile.from_dict(source).to_dict() == source

    def test_runtime_patch_validation_waits_for_composition(self):
        source = {
            "component": {
                "run": {"kind": "job", "container": {"image": "base:v1"}},
            },
            "run": {"kind": "service", "container": {"image": "service:v2"}},
            "runPatch": {"ports": [8080]},
        }
        config = V1Polyaxonfile.from_dict(source)

        assert isinstance(config.component.run, schemas.V1Job)
        assert isinstance(config.run, schemas.V1Service)
        assert config.run_patch == {"ports": [8080]}
        assert config.to_dict() == source

    def test_native_runtime_types_and_serialization(self):
        job = {
            "kind": "job",
            "container": {
                "image": "busybox:1.36",
                "resources": {
                    "requests": {"cpu": "500m"},
                    "limits": {"nvidia.com/gpu": 1, "google.com/tpu": 8},
                },
            },
        }
        for run, run_type in (
            (job, schemas.V1Job),
            (
                {
                    "kind": "service",
                    "ports": [8080],
                    "container": {"image": "notebook:v1"},
                },
                schemas.V1Service,
            ),
            (
                {
                    "kind": "pytorchjob",
                    "worker": {"replicas": 2, "container": {"image": "trainer:v1"}},
                },
                schemas.V1PytorchJob,
            ),
            (
                {
                    "kind": "dag",
                    "components": [{"name": "template", "run": job}],
                    "operations": [{"name": "train", "dagRef": "template"}],
                },
                schemas.V1Dag,
            ),
        ):
            with self.subTest(runtime=run["kind"]):
                config = V1Polyaxonfile.from_dict({"run": run})
                assert isinstance(config.run, run_type)
                assert config.get_run_kind() == run["kind"]
                assert config.to_dict() == {"run": run}

    def test_rejects_malformed_fields(self):
        for source in (
            {"kind": "compiled_operation"},
            {"kind": "polyaxonfile"},
            {"inputs": "count"},
            {"params": "count=3"},
            {"params": {"count": {"value": 3, "contextOnly": "invalid"}}},
            {"matrix": {"kind": "unknown"}},
            {"schedule": {"kind": "unknown"}},
            {"patchStrategy": "unknown"},
            {"component": {"unknown": True}},
            {"hubRef": "train:v1", "pathRef": "train.yaml"},
            {"runPatch": "echo hello"},
            {"run": "echo hello"},
            {"run": ["echo hello"]},
            {"run": {"kind": "unknown"}},
        ):
            with self.subTest(source=source), self.assertRaises(ValidationError):
                V1Polyaxonfile.from_dict(source)

    def test_rejects_unsupported_shortcuts_and_compiled_only_fields(self):
        for field in (
            "cmd",
            "env",
            "resources",
            "ports",
            "dag",
            "contexts",
        ):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                V1Polyaxonfile.from_dict({field: {}})

    def test_legacy_readers_use_shared_models_and_keep_defaults(self):
        assert ComponentSpecification.CONFIG is V1Component
        assert OperationSpecification.CONFIG is V1Operation
        run = {"kind": "job", "container": {"image": "busybox:1.36"}}

        for model, kind in ((V1Component, "component"), (V1Operation, "operation")):
            config = model.from_dict({"run": run, "params": {"count": 3}})
            assert config.kind == kind
            assert "kind" not in config.model_fields_set
            assert config.params["count"].value == 3
            assert config.to_dict() == {"run": run, "params": {"count": {"value": 3}}}

        assert V1Component.from_dict({"run": run}).to_dict() == {"run": run}
        source = {"component": {"run": run}}
        operation = V1Operation.from_dict(source)
        assert operation.to_dict() == source
        assert isinstance(operation.component, V1Component)
        assert operation.component.kind == "component"
