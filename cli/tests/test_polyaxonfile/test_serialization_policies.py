from copy import deepcopy
import json
import os
from pathlib import Path
import pytest
import subprocess
import sys
from textwrap import dedent
from unittest.mock import patch
import uuid

from polyaxon._flow.polyaxonfile import V1Component, V1Operation
from polyaxon._flow.run.dag import V1Dag
from polyaxon._polyaxonfile import CompiledOperationSpecification, read_polyaxonfile
from polyaxon._utils.test_utils import BaseTestCase


STATE_NAMESPACE = uuid.UUID("9b0a3806e3f84ea1959a7842e34129ed")
ENVIRONMENT_NULL_STATES = {
    ("kind", "environment", "operations"): "dddfca9f-f27f-549f-8a38-6d20a4b023e7",
    ("kind", "operations", "environment"): "f7c5cbdb-4479-5077-a33e-a4f8bbdc1b60",
}


def dag_source(explicit_nulls=False, environment_null=False):
    node = {
        "kind": "operation",
        "name": "train",
        "component": {
            "kind": "component",
            "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
        },
    }
    if explicit_nulls:
        node.update({"schedule": None, "matrix": None})
    source = {"kind": "component", "run": {"kind": "dag", "operations": [node]}}
    if environment_null:
        source["run"]["environment"] = None
    return source


def nested_dag_source():
    source = dag_source(explicit_nulls=True, environment_null=True)
    source["run"]["components"] = [
        {"kind": "component", "name": "nested", "run": deepcopy(source["run"])}
    ]
    source["run"]["operations"].append(
        {"kind": "operation", "name": "nested", "dagRef": "nested"}
    )
    return source


@pytest.mark.polyaxonfile_mark
class TestSerializationPolicies(BaseTestCase):
    def test_component_state_keeps_literal_job_states_and_authored_kind(self):
        for kind in (None, "component", "operation"):
            for version, expected in (
                (None, "4de9f1f8-06b5-54dd-b723-3737aeee69d2"),
                (0.4, "18bbe3c5-bfc4-5721-94f9-cf16e712c676"),
            ):
                with self.subTest(kind=kind, version=version):
                    source = {"run": {"kind": "job", "container": {"image": "test"}}}
                    if kind:
                        source["kind"] = kind
                    if version is not None:
                        source["version"] = version
                    spec = read_polyaxonfile(source)
                    before_fields = spec.model_fields_set.copy()

                    payload = spec.to_component_state_json()

                    assert str(uuid.uuid5(STATE_NAMESPACE, payload)) == expected
                    assert json.loads(payload) == {**source, "kind": "component"}
                    assert spec.to_component_state_dict() == json.loads(payload)
                    assert json.loads(spec.to_source_json()) == source
                    assert spec.model_fields_set == before_fields
                    assert spec.kind == kind

    def test_component_state_pins_null_and_omitted_dag_states(self):
        for explicit_nulls, expected in (
            (False, "88eb9eca-d36f-5763-8d24-5a645a86b700"),
            (True, "a7ae3b97-2926-5e14-991b-3b9747c8759a"),
        ):
            with self.subTest(explicit_nulls=explicit_nulls):
                source = dag_source(explicit_nulls=explicit_nulls)
                spec = read_polyaxonfile(source)

                payload = spec.to_component_state_json()

                assert json.loads(payload) == source
                assert str(uuid.uuid5(STATE_NAMESPACE, payload)) == expected
                assert json.loads(spec.to_source_json()) == source

    def test_component_state_preserves_both_legacy_environment_null_orders(self):
        source = dag_source(environment_null=True)
        spec = read_polyaxonfile(source)

        for order, expected in ENVIRONMENT_NULL_STATES.items():
            with self.subTest(order=order):
                fields = tuple(field for field in order if field != "kind") + (
                    "components",
                )
                with patch.object(V1Dag, "_CUSTOM_DUMP_FIELDS", fields):
                    payload = spec.to_component_state_json()

                assert json.loads(payload) == source
                assert tuple(json.loads(payload)["run"]) == order
                assert str(uuid.uuid5(STATE_NAMESPACE, payload)) == expected

    def test_component_state_matches_the_previous_normalization_pipeline(self):
        job = {"kind": "job", "container": {"image": "test"}}
        sources = [
            {},
            {"kind": None, "version": None, "queue": None, "run": job},
            {
                "strictParams": False,
                "params": {
                    "nothing": None,
                    "unset": {},
                    "empty": {"value": {}},
                    "options": {"value": {"items": [1, None, False]}},
                },
                "run": job,
            },
            {
                "inputs": [{"name": "count", "type": "int", "value": None}],
                "outputs": [{"name": "result", "type": "int"}],
                "run": job,
            },
            {
                "kind": "operation",
                "hubRef": "train:v1",
                "component": {"queue": None, "run": job},
                "run": {"container": {"args": ["override"]}},
                "runPatch": {"container": {"image": None}},
            },
            {
                "kind": "operation",
                "schedule": None,
                "matrix": None,
                "component": {
                    "schedule": {"kind": "cron", "cron": "0 * * * *"},
                    "matrix": {
                        "kind": "grid",
                        "params": {"seed": {"kind": "choice", "value": [1, 2]}},
                    },
                    "run": job,
                },
            },
            {
                "run": {
                    "kind": "service",
                    "environment": None,
                    "container": {"image": "test"},
                }
            },
            {"run": {"kind": "dag", "concurrency": None, "operations": "{{ nodes }}"}},
            dag_source(explicit_nulls=True, environment_null=True),
            nested_dag_source(),
        ]

        for source in sources:
            with self.subTest(source=source):
                spec = read_polyaxonfile(deepcopy(source))
                before = spec.to_source_json()
                previous = V1Component.read({**spec.to_dict(), "kind": "component"})

                assert spec.to_component_state_json() == previous.to_json()
                assert spec.to_source_json() == before

    def test_named_policies_ignore_generic_class_dump_defaults(self):
        source = dag_source(explicit_nulls=True, environment_null=True)
        source["kind"] = "operation"
        source["queue"] = None
        source["run"]["concurrency"] = None
        spec = read_polyaxonfile(source)
        compiled = CompiledOperationSpecification.read(
            {**source, "kind": "compiled_operation"}
        )
        before_source = spec.to_source_json()
        before_compiled = compiled.to_compiled_json()
        before_state = spec.to_component_state_json()

        with patch.dict(
            V1Dag._DUMP_POLICY,
            {"default": {"exclude_none": True}},
        ):
            assert "environment" not in spec.to_dict()["run"]
            assert spec.to_source_json() == before_source
            assert compiled.to_compiled_json() == before_compiled
            assert spec.to_component_state_json() == before_state

        assert json.loads(before_source) == source
        assert json.loads(before_compiled) == {
            "kind": "compiled_operation",
            "run": source["run"],
        }
        assert json.loads(before_state) == {"kind": "component", "run": source["run"]}

    def test_persistence_policies_do_not_change_component_state_input(self):
        source = dag_source(explicit_nulls=True, environment_null=True)
        spec = read_polyaxonfile(source)
        compiled = CompiledOperationSpecification.read(
            {**source, "kind": "compiled_operation"}
        )
        before_state = spec.to_component_state_json()
        before_source = spec.to_source_json()
        before_compiled = compiled.to_compiled_json()
        state_policy = deepcopy(V1Dag._DUMP_POLICY["component_state"])

        for purpose in ("source", "compiled"):
            with self.subTest(purpose=purpose):
                with patch.dict(
                    V1Dag._DUMP_POLICY,
                    {purpose: {"exclude_none": True}},
                ):
                    if purpose == "source":
                        assert spec.to_source_json() != before_source
                    else:
                        assert compiled.to_compiled_json() != before_compiled
                    assert spec.to_component_state_json() == before_state
                    assert V1Dag._DUMP_POLICY["component_state"] == state_policy

        assert spec.to_source_json() == before_source
        assert compiled.to_compiled_json() == before_compiled

    def test_component_state_is_single_pass_without_mutating_or_aliasing_source(self):
        source = nested_dag_source()
        source["kind"] = "operation"
        source["queue"] = None
        source["params"] = {"options": {"value": {"items": [1, {"value": None}]}}}
        spec = read_polyaxonfile(source)
        template = spec.run.components[0]
        node = spec.run.operations[0]
        models = (
            spec,
            spec.run,
            template,
            template.run,
            node,
            node.component,
            node.component.run,
            spec.params["options"],
        )
        before = spec.to_source_json()
        fields_sets = [model.model_fields_set.copy() for model in models]
        before_policy = deepcopy(V1Dag._DUMP_POLICY)
        expected = {**source, "kind": "component"}
        expected.pop("queue")

        for method in ("to_component_state_dict", "to_component_state_json"):
            with self.subTest(method=method):
                with patch.object(
                    V1Component, "obj_to_dict", wraps=V1Component.obj_to_dict
                ) as component_dump:
                    with patch.object(
                        V1Operation, "obj_to_dict", wraps=V1Operation.obj_to_dict
                    ) as operation_dump:
                        with patch.object(
                            V1Dag, "obj_to_dict", wraps=V1Dag.obj_to_dict
                        ) as dag_dump:
                            payload = getattr(spec, method)()

                if method == "to_component_state_json":
                    payload = json.loads(payload)
                assert payload == expected
                assert component_dump.call_count == 4
                assert operation_dump.call_count == 3
                assert dag_dump.call_count == 2
                dag_dump.assert_any_call(
                    spec.run, exclude_none=True, purpose="component_state"
                )
                dag_dump.assert_any_call(
                    template.run, exclude_none=False, purpose="component_state"
                )
                payload["params"]["options"]["value"]["items"][1]["value"] = "changed"
                payload["run"]["operations"][0]["schedule"] = "changed"
                payload["run"]["components"][0]["run"]["environment"] = "changed"
                assert spec.to_source_json() == before
                assert spec.to_component_state_dict() == expected
                assert [model.model_fields_set for model in models] == fields_sets
                assert spec.kind == "operation"
                assert spec.run.dag == {}
                assert template.run.dag == {}
                assert V1Dag._DUMP_POLICY == before_policy

    def test_component_state_matches_legacy_bytes_across_hash_seeds(self):
        sources = {
            "job": {"run": {"kind": "job", "container": {"image": "test"}}},
            "dag-omitted": dag_source(),
            "dag-node-nulls": dag_source(explicit_nulls=True),
            "dag-environment-null": dag_source(environment_null=True),
            "nested-dag": nested_dag_source(),
        }
        expected_states = {
            "job": "4de9f1f8-06b5-54dd-b723-3737aeee69d2",
            "dag-omitted": "88eb9eca-d36f-5763-8d24-5a645a86b700",
            "dag-node-nulls": "a7ae3b97-2926-5e14-991b-3b9747c8759a",
        }
        script = dedent(
            """
            import json
            import sys
            import uuid
            from polyaxon._polyaxonfile import read_polyaxonfile
            from polyaxon.schemas import V1Component

            namespace = uuid.UUID("9b0a3806e3f84ea1959a7842e34129ed")
            results = {}
            for name, source in json.loads(sys.argv[1]).items():
                spec = read_polyaxonfile(source)
                previous = V1Component.read({**spec.to_dict(), "kind": "component"})
                payload = spec.to_component_state_json()
                results[name] = {
                    "previous": previous.to_json(),
                    "payload": payload,
                    "state": str(uuid.uuid5(namespace, payload)),
                }
            print(json.dumps(results))
            """
        )
        for seed in (0, 1, 2, 42):
            with self.subTest(seed=seed):
                result = subprocess.run(
                    [sys.executable, "-B", "-c", script, json.dumps(sources)],
                    cwd=Path(__file__).resolve().parents[2],
                    env={**os.environ, "PYTHONHASHSEED": str(seed)},
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=60,
                )
                states = json.loads(result.stdout)
                for name, values in states.items():
                    assert values["payload"] == values["previous"], (seed, name)
                    if name in expected_states:
                        assert values["state"] == expected_states[name], (seed, name)
                    elif name == "dag-environment-null":
                        data = json.loads(values["payload"])
                        assert data == sources[name]
                        assert (
                            values["state"]
                            == ENVIRONMENT_NULL_STATES[tuple(data["run"])]
                        )
