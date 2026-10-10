from copy import deepcopy
import pytest

from clipped.config.patch_strategy import PatchStrategy
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
    compose_polyaxonfile,
    get_ops_from_suggestions,
    read_polyaxonfile,
)
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonValidationError


@pytest.mark.polyaxonfile_mark
class TestSharedMatrix(BaseTestCase):
    def test_direct_and_legacy_sources_create_independent_children(self):
        native = {
            "inputs": [
                {"name": "count", "type": "int"},
                {"name": "rate", "type": "float"},
            ],
            "outputs": [{"name": "result", "type": "str", "value": "done"}],
            "run": {
                "kind": "job",
                "container": {
                    "image": "busybox:1.36",
                    "command": ["sh", "-c"],
                    "args": ["echo '{{ count }} {{ rate }} {{ message }} {{ fixed }}'"],
                    "resources": {"limits": {"nvidia.com/gpu": 1}},
                },
            },
        }
        invocation = {
            "strictParams": True,
            "cache": {"disable": True},
            "params": {
                "count": {"value": 0, "contextOnly": False},
                "rate": 0.5,
                "message": {"value": "fallback", "contextOnly": True},
                "fixed": {
                    "value": "hello",
                    "contextOnly": True,
                    "toEnv": "FIXED",
                },
                "payload": {"value": {"items": [1, 2]}, "contextOnly": True},
            },
            "matrix": {
                "kind": "grid",
                "params": {
                    "count": {"kind": "choice", "value": [1, 2]},
                    "message": {"kind": "choice", "value": ["updated"]},
                },
            },
        }
        sources = [
            {**native, **invocation},
            {"kind": "component", **native, **invocation},
            {"kind": "operation", **native, **invocation},
            {"kind": "operation", "component": native, **invocation},
        ]
        for source in sources:
            with self.subTest(source=source):
                authored = read_polyaxonfile(source)
                before = authored.to_dict()
                parent, params = OperationSpecification.compile_operation_with_params(
                    authored
                )
                parent.apply_params(params)
                parent = CompiledOperationSpecification.apply_operation_contexts(parent)
                parent_before = parent.to_dict()
                suggestions = [
                    {"count": 1, "message": "updated"},
                    {"count": 2, "message": "updated"},
                ]
                suggestions_before = deepcopy(suggestions)

                children = list(
                    get_ops_from_suggestions(authored.to_json(), parent, suggestions)
                )

                assert len(children) == 2
                for count, child in enumerate(children, 1):
                    assert child.kind == authored.kind
                    assert (child.component is None) == (authored.component is None)
                    assert child.matrix is None
                    assert child.strict_params is True
                    assert set(child.params) == {"count", "message", "fixed", "payload"}
                    assert child.params["count"].value == count
                    assert child.params["count"].context_only is False
                    assert child.params["fixed"].to_env == "FIXED"
                    assert child.cache == parent.cache
                    runtime_source = child.component or child
                    assert runtime_source.run == parent.run
                    assert runtime_source.inputs == parent.inputs
                    assert runtime_source.outputs == parent.outputs
                    child_before = child.to_dict()

                    compiled, child_params = (
                        OperationSpecification.compile_operation_with_params(
                            read_polyaxonfile(child.to_json())
                        )
                    )
                    with self.assertRaises(PolyaxonValidationError):
                        compiled.validate_params(
                            params={**child_params, "count": {"value": "invalid"}},
                            is_template=False,
                        )
                    compiled.apply_params(child_params)
                    compiled = CompiledOperationSpecification.apply_operation_contexts(
                        compiled
                    )
                    compiled = CompiledOperationSpecification.apply_runtime_contexts(
                        compiled
                    )

                    assert compiled.strict_params is None
                    assert {io.name: io.value for io in compiled.inputs} == {
                        "count": count,
                        "rate": 0.5,
                    }
                    assert {io.name: io.value for io in compiled.contexts} == {
                        "message": "updated",
                        "fixed": "hello",
                        "payload": {"items": [1, 2]},
                    }
                    assert compiled.run.container.args == [
                        f"echo '{count} 0.5 updated hello'"
                    ]
                    assert compiled.run.container.resources == {
                        "limits": {"nvidia.com/gpu": 1}
                    }
                    assert child.to_dict() == child_before

                second_before = children[1].to_dict()
                first_runtime = children[0].component or children[0]
                first_runtime.run.container.image = "changed"
                first_runtime.run.container.resources["limits"]["nvidia.com/gpu"] = 8
                first_runtime.inputs[0].value = 99
                first_runtime.outputs[0].value = "changed"
                children[0].params["fixed"].value = "changed"
                children[0].params["payload"].value["items"].append(3)
                children[0].cache.disable = False
                assert children[1].to_dict() == second_before
                assert parent.to_dict() == parent_before
                assert authored.to_dict() == before
                assert suggestions == suggestions_before

    def test_nested_parent_fields_and_overrides_do_not_return_in_children(self):
        parent_fields = {
            "matrix": {
                "kind": "grid",
                "params": {"count": {"kind": "choice", "value": [1]}},
            },
            "schedule": {"kind": "interval", "frequency": 60},
            "conditions": "true",
            "events": [{"kinds": ["run_status_scheduled"], "ref": "ops.upstream"}],
            "dependencies": ["upstream"],
            "trigger": "all_succeeded",
            "build": {"hubRef": "builder"},
            "isApproved": True,
            "skipOnUpstreamSkip": True,
        }
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
                layer = {
                    **parent_fields,
                    "patchStrategy": strategy,
                    "inputs": [{"name": "count", "type": "int"}],
                    "outputs": [{"name": "result", "type": "str", "value": "old"}],
                    "cache": {"disable": False},
                    "queue": "old/queue",
                    "namespace": "old",
                    "strictParams": True,
                    "run": {"kind": "job", "container": {"image": "source:v1"}},
                    "container": {"image": "root:v1"},
                    "cmd": "echo root",
                    "runPatch": {"container": {"image": "patch:v2"}},
                }
                authored = read_polyaxonfile(
                    {
                        **deepcopy(layer),
                        "kind": "operation",
                        "hubRef": "org/train:v1",
                        "component": {
                            **deepcopy(layer),
                            "pathRef": "base.yaml",
                            "component": deepcopy(layer),
                        },
                    }
                )
                before = authored.to_dict()
                parent = OperationSpecification.compile_operation(authored)
                parent.run.container.image = "resolved:v3"
                parent.outputs[0].value = "resolved"
                parent.cache.disable = True
                parent.queue = "resolved/queue"
                parent.namespace = "resolved"

                child = next(get_ops_from_suggestions(authored, parent, [{"count": 3}]))

                assert child.hub_ref == "org/train:v1"
                assert child.component.path_ref == "base.yaml"
                assert child.component.component is not None
                current = child
                while current is not None:
                    for field in (
                        "matrix",
                        "schedule",
                        "conditions",
                        "events",
                        "dependencies",
                        "trigger",
                        "build",
                        "is_approved",
                        "skip_on_upstream_skip",
                        "container",
                        "cmd",
                        "run_patch",
                    ):
                        assert getattr(current, field) is None
                        assert field not in current.model_fields_set
                    if current is not child:
                        assert current.params is None
                        assert "params" not in current.model_fields_set
                    current = current.component

                for saved in (child, read_polyaxonfile(child.to_json())):
                    compiled, params = (
                        OperationSpecification.compile_operation_with_params(saved)
                    )
                    assert compiled.matrix is None
                    assert compiled.schedule is None
                    assert compiled.run == parent.run
                    assert compiled.inputs == parent.inputs
                    assert compiled.outputs == parent.outputs
                    assert compiled.cache == parent.cache
                    assert compiled.queue == parent.queue
                    assert compiled.namespace == parent.namespace
                    assert compiled.strict_params is True
                    assert params["count"].value == 3
                assert authored.to_dict() == before

    def test_suggestion_metadata_uses_composed_params(self):
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
                authored = read_polyaxonfile(
                    {
                        "patchStrategy": strategy,
                        "strictParams": False,
                        "params": {
                            "count": {
                                "value": 1,
                                "contextOnly": True,
                                "connection": "local",
                                "toInit": False,
                                "toEnv": "LOCAL",
                            }
                        },
                        "component": {
                            "strictParams": True,
                            "params": {
                                "count": {
                                    "value": 0,
                                    "contextOnly": True,
                                    "connection": "base",
                                    "toInit": True,
                                    "toEnv": "BASE",
                                }
                            },
                            "matrix": {
                                "kind": "grid",
                                "params": {"count": {"kind": "choice", "value": [3]}},
                            },
                            "run": {"kind": "job", "container": {"image": "busybox"}},
                        },
                    }
                )
                parent = OperationSpecification.compile_operation(authored)

                child = next(
                    get_ops_from_suggestions(
                        authored, parent, [{"count": "{{ 1 + 2 }}"}]
                    )
                )

                param = child.params["count"]
                local_wins = strategy in (
                    PatchStrategy.POST_MERGE,
                    PatchStrategy.REPLACE,
                )
                assert param.value == 3
                assert param.context_only is True
                assert param.connection == ("local" if local_wins else "base")
                assert param.to_init is (not local_wins)
                assert param.to_env == ("LOCAL" if local_wins else "BASE")
                assert child.strict_params is True
                compiled = OperationSpecification.compile_operation(child)
                compiled.validate_params(params=child.params, is_template=False)
                with self.assertRaisesRegex(
                    PolyaxonValidationError, "undeclared param"
                ):
                    compiled.validate_params(
                        params={**child.params, "unknown": {"value": 1}},
                        is_template=False,
                    )

    def test_params_without_io_keep_resolved_context_values(self):
        for strict in (False, True):
            with self.subTest(strict=strict):
                flags = {"contextOnly": True} if strict else {}
                authored = read_polyaxonfile(
                    {
                        "strictParams": strict,
                        "params": {
                            "count": {"value": 0, **flags},
                            "message": {"value": "hello", **flags},
                        },
                        "matrix": {
                            "kind": "grid",
                            "params": {"count": {"kind": "choice", "value": [3]}},
                        },
                        "run": {
                            "kind": "job",
                            "container": {
                                "image": "busybox:1.36",
                                "args": ["{{ count }} {{ message }} {{ late }}"],
                            },
                        },
                    }
                )
                parent, params = OperationSpecification.compile_operation_with_params(
                    authored
                )
                parent.apply_params(
                    {
                        **params,
                        "message": {"value": "resolved", **flags},
                        "late": {
                            "value": "bound",
                            "contextOnly": True,
                            "toEnv": "LATE",
                        },
                    }
                )
                parent = CompiledOperationSpecification.apply_operation_contexts(parent)

                child = next(get_ops_from_suggestions(authored, parent, [{"count": 3}]))

                assert child.inputs is None
                assert child.outputs is None
                assert child.params["message"].value == "resolved"
                assert child.params["late"].context_only is True
                assert child.params["late"].to_env == "LATE"
                compiled, params = OperationSpecification.compile_operation_with_params(
                    read_polyaxonfile(child.to_json())
                )
                compiled.apply_params(params)
                compiled = CompiledOperationSpecification.apply_operation_contexts(
                    compiled
                )
                compiled = CompiledOperationSpecification.apply_runtime_contexts(
                    compiled
                )
                assert compiled.inputs is None
                assert {io.name: io.value for io in compiled.contexts} == {
                    "count": 3,
                    "message": "resolved",
                    "late": "bound",
                }
                assert compiled.run.container.args == ["3 resolved bound"]

    def test_service_distributed_and_dag_runtimes_are_preserved(self):
        matrix = {
            "kind": "grid",
            "params": {"count": {"kind": "choice", "value": [1]}},
        }
        container = {
            "image": "busybox:1.36",
            "args": ["{{ count }}"],
            "resources": {"limits": {"nvidia.com/gpu": 1}},
        }
        runtimes = [
            {"kind": "service", "ports": [8080], "container": container},
            {"kind": "pytorchjob", "worker": {"replicas": 2, "container": container}},
            {
                "kind": "dag",
                "operations": [
                    {
                        "name": "nested-matrix",
                        "matrix": matrix,
                        "run": {"kind": "job", "container": container},
                    }
                ],
            },
        ]
        for runtime in runtimes:
            with self.subTest(kind=runtime["kind"]):
                authored = read_polyaxonfile({"matrix": matrix, "run": runtime})
                parent = OperationSpecification.compile_operation(authored)

                child = next(get_ops_from_suggestions(authored, parent, [{"count": 1}]))

                effective = compose_polyaxonfile(read_polyaxonfile(child.to_json()))
                assert effective.matrix is None
                assert effective.run == parent.run
                assert effective.run.to_dict() == runtime
                compiled = OperationSpecification.compile_operation(child)
                assert compiled.run == parent.run
