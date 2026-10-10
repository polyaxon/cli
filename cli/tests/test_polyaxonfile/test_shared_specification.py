from collections import defaultdict
from copy import deepcopy
import json
from mock import patch
from pathlib import Path
import pytest
from tempfile import TemporaryDirectory
import yaml

from clipped.compact.pydantic import ValidationError
from polyaxon._config.spec import ConfigSpec
from polyaxon._flow.component.component import V1Component
from polyaxon._flow.operations.compiled_operation import V1CompiledOperation
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.params import V1Param
from polyaxon._flow.polyaxonfile import PartialV1Polyaxonfile, V1Polyaxonfile
from polyaxon._polyaxonfile import read_polyaxonfile
from polyaxon._polyaxonfile.specs import get_specification
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonfileError, PolyaxonSchemaError


@pytest.mark.polyaxonfile_mark
class TestSharedSpecification(BaseTestCase):
    def test_read_native_document_from_mapping_stream_and_file(self):
        source = {
            "inputs": [{"name": "count", "type": "int"}],
            "params": {"count": 3},
            "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
        }
        for kind in (None, "component", "operation"):
            authored = deepcopy(source)
            if kind:
                authored["kind"] = kind
            original = deepcopy(authored)
            expected = {**authored, "params": {"count": {"value": 3}}}
            with TemporaryDirectory() as directory:
                yaml_path = Path(directory) / "polyaxonfile.yaml"
                json_path = Path(directory) / "polyaxonfile.json"
                yaml_source = yaml.safe_dump(authored)
                json_source = json.dumps(authored)
                yaml_path.write_text(yaml_source)
                json_path.write_text(json_source)

                for value in (
                    authored,
                    yaml_source,
                    json_source,
                    str(yaml_path),
                    str(json_path),
                    ConfigSpec(str(yaml_path)),
                ):
                    with self.subTest(kind=kind, value=value):
                        config = read_polyaxonfile(value)

                        assert isinstance(config, V1Polyaxonfile)
                        assert config.kind == kind
                        assert config.version is None
                        assert config.params["count"].value == 3
                        assert config.run.container.image == "busybox:1.36"
                        assert config.to_dict() == expected
            assert authored == original

    def test_read_legacy_documents_without_changing_their_shape(self):
        component = {
            "version": 1.1,
            "kind": "component",
            "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
        }
        operation = {
            "version": 1.1,
            "kind": "operation",
            "hubRef": "train:v1",
            "component": component,
            "params": {"count": {"value": 3}},
            "runPatch": {"container": {"image": "local:v2"}},
        }
        for source in (component, operation):
            with self.subTest(kind=source["kind"]):
                config = read_polyaxonfile(json.dumps(source))

                assert config.version == 1.1
                assert config.to_dict() == source
                assert config.to_dict() == get_specification(source).to_dict()

    def test_preserve_supplied_null_false_and_empty_fields(self):
        source = {
            "kind": None,
            "version": None,
            "queue": None,
            "strictParams": False,
            "params": {},
            "presets": [],
            "component": {
                "queue": None,
                "inputs": [],
                "run": {"kind": "job", "container": None, "connections": []},
            },
        }
        config = read_polyaxonfile(json.dumps(source))

        assert config.model_fields_set == {
            "kind",
            "version",
            "queue",
            "strict_params",
            "params",
            "presets",
            "component",
        }
        assert config.kind is None
        assert config.version is None
        assert config.queue is None
        assert config.strict_params is False
        assert config.params == {}
        assert config.presets == []
        assert config.component.model_fields_set == {"queue", "inputs", "run"}
        assert config.component.queue is None
        assert config.component.inputs == []
        assert config.component.run.model_fields_set == {
            "kind",
            "container",
            "connections",
        }
        assert config.component.run.container is None
        assert config.component.run.connections == []
        assert json.loads(config.to_source_json()) == source

    def test_source_serialization_keeps_unset_fields_omitted(self):
        for kind in (None, "component", "operation"):
            for fields in ({}, {"queue": None, "schedule": None, "matrix": None}):
                with self.subTest(kind=kind, fields=fields):
                    source = dict(fields)
                    if kind:
                        source["kind"] = kind
                    config = read_polyaxonfile(source)
                    fields_set = config.model_fields_set.copy()

                    assert json.loads(config.to_source_json()) == source
                    assert config.model_fields_set == fields_set
                    assert "version" not in config.model_fields_set
                    assert config.to_dict() == ({"kind": kind} if kind else {})

    def test_source_serialization_preserves_nested_dag_definitions(self):
        source = {
            "schedule": None,
            "component": {
                "run": {
                    "kind": "dag",
                    "components": "{{ components }}",
                    "operations": [
                        {
                            "name": "nested",
                            "run": {
                                "kind": "dag",
                                "environment": None,
                                "concurrency": None,
                                "components": [
                                    {
                                        "name": "train",
                                        "queue": None,
                                        "run": {
                                            "kind": "job",
                                            "container": {"image": "busybox:1.36"},
                                        },
                                    }
                                ],
                                "operations": [
                                    {
                                        "name": "once",
                                        "dagRef": "train",
                                        "schedule": None,
                                        "matrix": None,
                                    },
                                    {"name": "inherited", "dagRef": "train"},
                                ],
                            },
                        }
                    ],
                }
            },
        }
        config = read_polyaxonfile(source)

        assert json.loads(config.to_source_json()) == source

    def test_source_serialization_does_not_mutate_source(self):
        source = {
            "queue": None,
            "params": {"options": {"value": {"items": [1, {"value": None}]}}},
            "component": {
                "queue": None,
                "run": {
                    "kind": "job",
                    "environment": None,
                    "container": {
                        "image": "busybox:1.36",
                        "args": ["{{ options }}"],
                    },
                },
            },
        }
        config = read_polyaxonfile(source)
        models = (
            config,
            config.component,
            config.component.run,
            config.params["options"],
        )
        fields_sets = [model.model_fields_set.copy() for model in models]
        compact = config.to_dict()

        assert json.loads(config.to_source_json()) == source

        assert config.to_dict() == compact
        assert [model.model_fields_set for model in models] == fields_sets

    def test_source_serializer_visits_each_definition_once(self):
        source = {
            "run": {
                "kind": "dag",
                "components": [
                    {
                        "kind": "component",
                        "name": "train",
                        "run": {
                            "kind": "job",
                            "container": {"image": "busybox:1.36"},
                        },
                    }
                ],
                "operations": [
                    {
                        "kind": "operation",
                        "name": "first",
                        "dagRef": "train",
                        "schedule": None,
                    },
                    {
                        "kind": "operation",
                        "name": "second",
                        "dagRef": "train",
                        "matrix": None,
                    },
                ],
            }
        }
        config = read_polyaxonfile(source)

        with patch.object(
            V1Operation, "obj_to_dict", wraps=V1Operation.obj_to_dict
        ) as operation_dump:
            with patch.object(
                V1Component, "obj_to_dict", wraps=V1Component.obj_to_dict
            ) as component_dump:
                payload = json.loads(config.to_source_json())

        assert payload == source
        assert operation_dump.call_count == 2
        component_dump.assert_called_once_with(
            config.run.components[0], exclude_none=False
        )

    def test_read_model_copies_nested_values_and_field_presence(self):
        source = V1Polyaxonfile.from_dict(
            {
                "params": {"count": 3},
                "component": {
                    "queue": None,
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                },
            }
        )
        config = read_polyaxonfile(source, is_preset=True)

        assert config is not source
        assert config.is_preset is True
        assert source.is_preset is None
        assert "is_preset" not in source.model_fields_set
        assert config.component.model_fields_set == source.component.model_fields_set
        assert "queue" in config.component.model_fields_set
        assert config.component.queue is None

        config.component.run.container.image = "local:v2"
        config.params["count"].value = 5
        assert source.component.run.container.image == "base:v1"
        assert source.params["count"].value == 3

    def test_read_model_preserves_type_values_and_unset_fields(self):
        for model in (V1Polyaxonfile, V1Component, V1Operation, PartialV1Polyaxonfile):
            with self.subTest(model=model):
                source = model.model_construct(
                    _fields_set={"component", "queue", "params", "presets"},
                    component=read_polyaxonfile(
                        {
                            "queue": None,
                            "strictParams": False,
                            "inputs": [],
                            "run": {"kind": "job", "container": None},
                        }
                    ),
                    queue=None,
                    params={},
                    presets=[],
                    strict_params=True,
                    version=1.1,
                    run_patch={"connections": ["artifacts"]},
                )

                config = read_polyaxonfile(source)

                assert type(config) is model
                assert config == deepcopy(source)
                assert config.model_fields_set == source.model_fields_set
                assert config.model_fields_set is not source.model_fields_set
                assert config.component.model_fields_set == (
                    source.component.model_fields_set
                )
                assert config.component.run.model_fields_set == {"kind", "container"}
                assert config.component.strict_params is False
                assert config.component.inputs == []
                assert config.params == {}
                assert config.presets == []
                assert config.queue is None
                assert config.strict_params is True
                assert config.version == 1.1
                config.run_patch["connections"].append("other")
                config.component.queue = "local"
                config.model_fields_set.add("name")
                assert source.run_patch == {"connections": ["artifacts"]}
                assert source.component.queue is None
                assert "name" not in source.model_fields_set

    def test_read_model_preserves_aliases_and_cycles_in_mutable_values(self):
        shared = {"items": []}
        param = V1Param.model_construct(value=shared)
        source = V1Polyaxonfile.model_construct(
            params={"first": param, "second": param}
        )
        shared["self"] = shared
        shared["source"] = source
        shared["items"].append(shared["items"])

        config = read_polyaxonfile(source)

        assert config.params["first"] is config.params["second"]
        assert config.params["first"] is not param
        copied = config.params["first"].value
        assert copied is not shared
        assert copied["self"] is copied
        assert copied["source"] is config
        assert copied["items"][0] is copied["items"]
        copied["items"].append("changed")
        assert len(shared["items"]) == 1

    def test_read_model_copies_private_dag_state_with_shared_nodes(self):
        source = read_polyaxonfile(
            {
                "run": {
                    "kind": "dag",
                    "operations": [
                        {"name": "task", "run": {"kind": "job"}},
                    ],
                }
            }
        )
        source.run._context = {"node": source.run.operations[0], "values": []}
        source.run._effective_ops = {"task": source.run.operations[0]}

        config = read_polyaxonfile(source)

        assert config.run._context["node"] is config.run.operations[0]
        assert config.run._effective_ops["task"] is config.run.operations[0]
        assert config.run.operations[0] is not source.run.operations[0]
        config.run._context["values"].append(1)
        config.run.operations[0].name = "changed"
        assert source.run._context["values"] == []
        assert source.run.operations[0].name == "task"

    def test_read_model_preserves_cached_attributes_and_their_aliases(self):
        source = V1Polyaxonfile.model_construct(
            params={"message": V1Param.model_construct(value={"items": []})}
        )
        source.__dict__["cached_value"] = source.params["message"].value

        config = read_polyaxonfile(source)

        assert config.__dict__["cached_value"] is config.params["message"].value
        assert config.model_fields_set == {"params"}
        config.__dict__["cached_value"]["items"].append(1)
        assert source.__dict__["cached_value"] == {"items": []}

    def test_read_model_respects_custom_deepcopy_hooks(self):
        class CustomFile(V1Polyaxonfile):
            def __deepcopy__(self, memo):
                result = type(self).model_construct(description="custom copy")
                memo[id(self)] = result
                return result

        source = V1Polyaxonfile.model_construct(component=CustomFile())

        config = read_polyaxonfile(source)

        assert type(config.component) is CustomFile
        assert config.component.description == "custom copy"
        assert source.component.description is None

    def test_read_model_does_not_invoke_custom_shallow_copy_hooks(self):
        def reject_copy(*args, **kwargs):
            raise AssertionError("Custom shallow copy must not replace deepcopy")

        for method in ("__copy__", "copy", "model_copy"):
            with self.subTest(method=method):

                class CustomFile(V1Polyaxonfile):
                    pass

                setattr(CustomFile, method, reject_copy)
                source = CustomFile.model_construct(params={})

                config = read_polyaxonfile(source)

                assert type(config) is CustomFile
                assert config.params == {}
                assert config.params is not source.params

    def test_read_model_preserves_extra_values(self):
        class ExtraFile(V1Polyaxonfile):
            class Config:
                extra = "allow"

        source = ExtraFile.from_dict({"extra_value": {"items": []}})

        config = read_polyaxonfile(source)

        assert type(config) is ExtraFile
        assert config.model_fields_set == source.model_fields_set
        config.extra_value["items"].append(1)
        assert source.extra_value == {"items": []}

    def test_read_model_preserves_references_to_model_metadata_in_either_order(self):
        for reverse in (False, True):
            param = V1Param.model_construct(value="message")
            params = {
                "message": param,
                "metadata": V1Param.model_construct(
                    value={
                        "attributes": param.__dict__,
                        "fields": param.model_fields_set,
                    }
                ),
            }
            if reverse:
                params = dict(reversed(list(params.items())))
            source = V1Polyaxonfile.model_construct(params=params)

            config = read_polyaxonfile(source)

            copied_param = config.params["message"]
            metadata = config.params["metadata"].value
            assert metadata["attributes"] is copied_param.__dict__
            assert metadata["fields"] is copied_param.model_fields_set
            metadata["fields"].add("name")
            assert "name" not in param.model_fields_set

    def test_read_model_falls_back_for_container_and_scalar_subclasses(self):
        class Label(str):
            pass

        label = Label("message")
        label.values = []
        values = defaultdict(list, {"message": label})
        source = V1Polyaxonfile.model_construct(
            params={"message": V1Param.model_construct(value=(values, label, {label}))}
        )

        config = read_polyaxonfile(source)

        copied_values, copied_label, copied_set = config.params["message"].value
        assert type(copied_values) is defaultdict
        assert copied_values.default_factory is list
        assert type(copied_label) is Label
        assert copied_values["message"] is copied_label
        assert next(iter(copied_set)) is copied_label
        assert copied_label is not label
        copied_label.values.append(1)
        copied_values["missing"].append(2)
        assert label.values == []
        assert "missing" not in values

    def test_read_incomplete_layers_without_adding_kind_or_version(self):
        for source in (
            {},
            {"params": {"count": {"value": 3}}},
            {"pathRef": "train.yaml"},
            {"isPreset": True, "queue": "gpu"},
            {"component": {"params": {"count": {"value": 3}}}},
            {"run": {"kind": "job"}},
        ):
            with self.subTest(source=source):
                config = read_polyaxonfile(json.dumps(source))

                assert config.to_dict() == source
                assert "kind" not in config.model_fields_set
                assert "version" not in config.model_fields_set
        assert read_polyaxonfile({}).model_fields_set == set()

    def test_partial_and_preset_layers_defer_reference_validation(self):
        source = {"hubRef": "train:v1", "pathRef": "train.yaml"}
        original = deepcopy(source)
        with self.assertRaisesRegex(ValidationError, "At most one reference"):
            read_polyaxonfile(source)

        for options in ({"partial": True}, {"is_preset": True}):
            with self.subTest(options=options):
                config = read_polyaxonfile(source, **options)

                assert config.hub_ref == "train:v1"
                assert config.path_ref == "train.yaml"
                assert config.is_preset is options.get("is_preset")
                assert ("is_preset" in config.model_fields_set) == bool(
                    options.get("is_preset")
                )
                assert source == original

        preset = read_polyaxonfile({**source, "isPreset": True})
        assert preset.hub_ref == "train:v1"
        assert preset.path_ref == "train.yaml"

    def test_preset_flag_accepts_alias_and_python_name_without_mutating_source(self):
        for field in ("isPreset", "is_preset"):
            source = {field: False, "queue": "gpu"}
            with self.subTest(field=field):
                config = read_polyaxonfile(source, is_preset=True)

                assert config.is_preset is True
                assert config.to_dict() == {"isPreset": True, "queue": "gpu"}
                assert source == {field: False, "queue": "gpu"}

    def test_empty_references_keep_legacy_validation_behavior(self):
        source = {"hubRef": "", "pathRef": "train.yaml"}
        config = read_polyaxonfile(source)

        assert config.to_dict() == V1Operation.from_dict(source).to_dict()
        assert config.hub_ref == ""
        assert config.path_ref == "train.yaml"

    def test_references_and_run_overrides_are_kept_without_loading_or_merging(self):
        for field, reference in (
            ("pathRef", "missing.yaml"),
            ("urlRef", "https://example.com/train.yaml"),
            ("hubRef", "train:v1"),
            ("dagRef", "train"),
        ):
            source = {
                field: reference,
                "component": {
                    "params": {"count": {"value": 1}},
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                },
                "params": {"count": {"value": 3}},
                "run": {"kind": "service", "container": {"image": "local:v2"}},
                "runPatch": {"ports": [8080]},
                "patchStrategy": "pre_merge",
            }
            with (
                self.subTest(reference=field),
                patch.object(ConfigSpec, "read_from_url") as read_url,
                patch.object(ConfigSpec, "read_from_custom_hub") as read_hub,
                patch.object(ConfigSpec, "read_from_file") as read_file,
            ):
                config = read_polyaxonfile(source)

                assert config.to_dict() == source
                assert config.component.run.container.image == "base:v1"
                assert config.run.container.image == "local:v2"
                assert config.run_patch == {"ports": [8080]}
                read_url.assert_not_called()
                read_hub.assert_not_called()
                read_file.assert_not_called()

    def test_partial_and_preset_loading_still_validate_field_types(self):
        for options in ({}, {"partial": True}, {"is_preset": True}):
            for source in (
                {"kind": "compiled_operation"},
                {"params": "count=3"},
                {"hubRef": ["train:v1"]},
                {"component": {"unknown": True}},
                {"run": {"kind": "unknown"}},
                {"cmd": 1},
                {"env": {"RETRIES": 3}},
                {"contexts": []},
            ):
                with (
                    self.subTest(options=options, source=source),
                    self.assertRaises(ValidationError),
                ):
                    read_polyaxonfile(source, **options)

    def test_reject_non_mapping_documents_and_source_lists(self):
        for source in ("[]", "null", "true", '"train"'):
            with (
                self.subTest(source=source),
                self.assertRaisesRegex(PolyaxonfileError, "must contain a mapping"),
            ):
                read_polyaxonfile(source)

        with TemporaryDirectory() as directory:
            path = Path(directory) / "empty.yaml"
            path.write_text("")
            with self.assertRaisesRegex(PolyaxonfileError, "must contain a mapping"):
                read_polyaxonfile(str(path))

        for source in (None, 3, [{"params": {"count": 3}}, {"queue": "gpu"}]):
            with self.subTest(source=source), self.assertRaises(PolyaxonSchemaError):
                read_polyaxonfile(source)

    def test_production_dispatch_uses_shared_models_and_keeps_compiled_separate(self):
        run = {"kind": "job", "container": {"image": "busybox:1.36"}}
        for source, model in (
            ({"kind": "component", "run": run}, V1Component),
            ({"kind": "operation", "component": {"run": run}}, V1Operation),
            ({"kind": "component", "run": run, "params": {}}, V1Component),
            ({"kind": "operation", "run": run}, V1Operation),
            ({"run": run}, V1Polyaxonfile),
            ({"kind": "compiled_operation", "run": run}, V1CompiledOperation),
        ):
            with self.subTest(kind=source.get("kind")):
                assert isinstance(get_specification(source), model)
        assert not issubclass(V1CompiledOperation, V1Polyaxonfile)
