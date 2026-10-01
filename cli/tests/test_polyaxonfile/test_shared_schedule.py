from copy import deepcopy
from datetime import timedelta
import pytest

from clipped.config.patch_strategy import PatchStrategy
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
    compose_polyaxonfile,
    get_op_from_schedule,
    get_ops_from_suggestions,
    read_polyaxonfile,
)
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonValidationError


@pytest.mark.polyaxonfile_mark
class TestSharedSchedule(BaseTestCase):
    def test_jobs_and_services_keep_params_and_independent_copies(self):
        for runtime in ("job", "service"):
            native = {
                "inputs": [{"name": "count", "type": "int"}],
                "outputs": [{"name": "result", "type": "str", "value": "done"}],
                "run": {
                    "kind": runtime,
                    "container": {
                        "image": "busybox:1.36",
                        "command": ["sh", "-c"],
                        "args": ["echo {{ count }} {{ message }}"],
                        "resources": {"limits": {"nvidia.com/gpu": 1}},
                    },
                },
            }
            if runtime == "service":
                native["run"]["ports"] = [8080]
            invocation = {
                "schedule": {"kind": "interval", "frequency": 60},
                "strictParams": True,
                "cache": {"disable": True},
                "isApproved": True,
                "params": {
                    "count": {"value": 3, "contextOnly": False},
                    "message": {
                        "value": "hello",
                        "contextOnly": True,
                        "connection": "data",
                        "toInit": True,
                        "toEnv": "MESSAGE",
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
                with self.subTest(runtime=runtime, kind=source.get("kind")):
                    authored = read_polyaxonfile(source)
                    before = authored.to_dict()
                    parent, params = (
                        OperationSpecification.compile_operation_with_params(authored)
                    )
                    parent.apply_params(params)
                    parent = CompiledOperationSpecification.apply_operation_contexts(
                        parent
                    )
                    parent_before = parent.to_dict()

                    first = get_op_from_schedule(authored.to_json(), parent)
                    second = get_op_from_schedule(authored.to_json(), parent)

                    for child in (first, second):
                        assert child.kind == authored.kind
                        assert (child.component is None) == (authored.component is None)
                        assert child.schedule is None
                        assert child.is_approved is True
                        assert child.strict_params is True
                        assert child.params == authored.params
                        component = child.component or child
                        assert component.run == parent.run
                        assert component.inputs == parent.inputs
                        assert component.outputs == parent.outputs
                        child_before = child.to_dict()
                        compiled, child_params = (
                            OperationSpecification.compile_operation_with_params(
                                read_polyaxonfile(child.to_json())
                            )
                        )
                        with self.assertRaisesRegex(
                            PolyaxonValidationError, "undeclared param"
                        ):
                            compiled.validate_params(
                                params={**child_params, "unknown": {"value": 1}},
                                is_template=False,
                            )
                        compiled.apply_params(child_params)
                        compiled = (
                            CompiledOperationSpecification.apply_operation_contexts(
                                compiled
                            )
                        )
                        compiled = (
                            CompiledOperationSpecification.apply_runtime_contexts(
                                compiled
                            )
                        )
                        assert compiled.strict_params is None
                        assert compiled.inputs[0].value == 3
                        assert compiled.contexts[0].value == "hello"
                        assert compiled.contexts[0].connection == "data"
                        assert compiled.contexts[0].to_init is True
                        assert compiled.contexts[0].to_env == "MESSAGE"
                        assert compiled.run.container.args == ["echo 3 hello"]
                        assert compiled.run.container.resources == {
                            "limits": {"nvidia.com/gpu": 1}
                        }
                        if runtime == "service":
                            assert compiled.run.ports == [8080]
                        assert child.to_dict() == child_before

                    second_before = second.to_dict()
                    component = first.component or first
                    component.run.container.image = "changed"
                    component.run.container.resources["limits"]["nvidia.com/gpu"] = 8
                    component.inputs[0].value = 99
                    component.outputs[0].value = "changed"
                    first.params["message"].value = "changed"
                    first.cache.disable = False
                    assert second.to_dict() == second_before
                    assert parent.to_dict() == parent_before
                    assert authored.to_dict() == before

    def test_nested_layers_keep_child_fields_and_remove_parent_fields(self):
        parent_fields = {
            "schedule": {"kind": "interval", "frequency": 60},
            "conditions": "true",
            "events": [{"kinds": ["run_status_scheduled"], "ref": "ops.upstream"}],
            "dependencies": ["upstream"],
            "trigger": "all_succeeded",
            "build": {"hubRef": "builder"},
            "skipOnUpstreamSkip": True,
        }
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
                base = {
                    **parent_fields,
                    "strictParams": True,
                    "cache": {"disable": False},
                    "queue": "base/queue",
                    "namespace": "base",
                    "inputs": [{"name": "count", "type": "int"}],
                    "outputs": [{"name": "result", "type": "str", "value": "old"}],
                    "params": {"count": 1},
                    "isApproved": True,
                    "matrix": {
                        "kind": "grid",
                        "concurrency": 1,
                        "params": {"seed": {"kind": "choice", "value": [1, 2]}},
                    },
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                }
                local = {
                    **parent_fields,
                    "patchStrategy": strategy,
                    "strictParams": False,
                    "cache": {"disable": False},
                    "queue": "local/queue",
                    "namespace": "local",
                    "inputs": [{"name": "count", "type": "int"}],
                    "params": {"count": 3},
                    "isApproved": False,
                    "matrix": {
                        "kind": "grid",
                        "concurrency": 2,
                        "params": {"seed": {"kind": "choice", "value": [3, 4]}},
                    },
                    "run": {"kind": "job", "container": {"image": "local:v2"}},
                    "runPatch": {"container": {"image": "patch:v3"}},
                }
                authored = read_polyaxonfile(
                    {
                        **local,
                        "kind": "operation",
                        "hubRef": "org/train:v1",
                        "component": {
                            **deepcopy(local),
                            "pathRef": "base.yaml",
                            "component": base,
                        },
                    }
                )
                before = authored.to_dict()
                parent, params = OperationSpecification.compile_operation_with_params(
                    authored
                )
                parent.run.container.image = "resolved:v4"
                parent.outputs[0].value = "resolved"
                parent.cache.disable = True
                parent.queue = "resolved/queue"
                parent.namespace = "resolved"

                child = get_op_from_schedule(authored, parent)

                assert child.hub_ref == authored.hub_ref
                assert child.component.path_ref == "base.yaml"
                current, original = child, authored
                while current is not None:
                    assert current.params == original.params
                    assert current.matrix == original.matrix
                    assert current.is_approved == original.is_approved
                    for field in ("params", "matrix", "is_approved"):
                        assert (field in current.model_fields_set) == (
                            field in original.model_fields_set
                        )
                    for field in (
                        "schedule",
                        "conditions",
                        "events",
                        "dependencies",
                        "trigger",
                        "build",
                        "skip_on_upstream_skip",
                        "run_patch",
                    ):
                        assert getattr(current, field) is None
                        assert field not in current.model_fields_set
                    current, original = current.component, original.component

                for saved in (child, read_polyaxonfile(child.to_json())):
                    compiled, child_params = (
                        OperationSpecification.compile_operation_with_params(saved)
                    )
                    assert compiled.schedule is None
                    assert compiled.run == parent.run
                    assert compiled.inputs == parent.inputs
                    assert compiled.outputs == parent.outputs
                    assert compiled.cache == parent.cache
                    assert compiled.queue == parent.queue
                    assert compiled.namespace == parent.namespace
                    assert compiled.strict_params is True
                    assert compiled.matrix == parent.matrix
                    assert compiled.is_approved == parent.is_approved
                    assert child_params == params
                local_wins = strategy in (
                    PatchStrategy.POST_MERGE,
                    PatchStrategy.REPLACE,
                )
                assert params["count"].value == (3 if local_wins else 1)
                assert parent.is_approved is (not local_wins)
                assert authored.to_dict() == before

    def test_scheduled_matrix_keeps_approval_until_suggestions_create_jobs(self):
        authored = read_polyaxonfile(
            {
                "component": {
                    "kind": "operation",
                    "strictParams": True,
                    "schedule": {"kind": "interval", "frequency": 60},
                    "matrix": {
                        "kind": "grid",
                        "params": {"count": {"kind": "choice", "value": [1, 2]}},
                    },
                    "isApproved": False,
                    "inputs": [{"name": "count", "type": "int"}],
                    "params": {"message": {"value": "hello", "contextOnly": True}},
                    "run": {
                        "kind": "job",
                        "container": {
                            "image": "busybox:1.36",
                            "args": ["echo {{ count }} {{ message }}"],
                        },
                    },
                }
            }
        )
        before = authored.to_dict()
        parent, params = OperationSpecification.compile_operation_with_params(authored)
        parent.apply_params(params)
        parent = CompiledOperationSpecification.apply_operation_contexts(parent)

        occurrence = get_op_from_schedule(authored, parent)

        assert occurrence.params is None
        assert occurrence.component.params == authored.component.params
        assert occurrence.component.schedule is None
        assert occurrence.component.is_approved is False
        assert occurrence.component.matrix == authored.component.matrix
        saved = read_polyaxonfile(occurrence.to_json())
        compiled, params = OperationSpecification.compile_operation_with_params(saved)
        compiled.apply_params(params)
        compiled = CompiledOperationSpecification.apply_operation_contexts(compiled)
        assert compiled.schedule is None
        assert compiled.matrix.kind == "grid"
        assert compiled.strict_params is True
        assert compiled.is_approved == parent.is_approved
        occurrence_before = occurrence.to_dict()

        jobs = list(
            get_ops_from_suggestions(
                occurrence.to_json(), compiled, [{"count": 1}, {"count": 2}]
            )
        )

        assert len(jobs) == 2
        for count, job in enumerate(jobs, 1):
            compiled, params = OperationSpecification.compile_operation_with_params(job)
            assert compiled.matrix is None
            assert compiled.schedule is None
            assert compiled.is_approved is None
            assert compiled.strict_params is True
            assert params["message"].context_only is True
            compiled.apply_params(params)
            compiled = CompiledOperationSpecification.apply_operation_contexts(compiled)
            compiled = CompiledOperationSpecification.apply_runtime_contexts(compiled)
            assert compiled.run.container.args == [f"echo {count} hello"]
        assert occurrence.to_dict() == occurrence_before
        assert authored.to_dict() == before

    def test_context_params_use_each_occurrence_globals(self):
        for strict in (False, True):
            with self.subTest(strict=strict):
                param = {"value": "{{ globals.uuid }}", "toEnv": "RUN_ID"}
                if strict:
                    param["contextOnly"] = True
                authored = read_polyaxonfile(
                    {
                        "schedule": {"kind": "interval", "frequency": 60},
                        "strictParams": strict,
                        "params": {"run_id": param},
                        "run": {
                            "kind": "job",
                            "container": {
                                "image": "busybox:1.36",
                                "args": ["echo {{ run_id }}"],
                            },
                        },
                    }
                )
                parent, params = OperationSpecification.compile_operation_with_params(
                    authored
                )
                parent.apply_params(params)
                parent = CompiledOperationSpecification.apply_operation_contexts(
                    parent, contexts={"globals": {"uuid": "parent"}}
                )
                assert parent.contexts[0].value == "parent"

                for identity in ("first", "second"):
                    child = get_op_from_schedule(authored, parent)
                    assert child.params["run_id"].value == "{{ globals.uuid }}"
                    compiled, params = (
                        OperationSpecification.compile_operation_with_params(
                            read_polyaxonfile(child.to_json())
                        )
                    )
                    compiled.apply_params(params)
                    compiled = CompiledOperationSpecification.apply_operation_contexts(
                        compiled, contexts={"globals": {"uuid": identity}}
                    )
                    compiled = CompiledOperationSpecification.apply_runtime_contexts(
                        compiled
                    )
                    assert compiled.inputs is None
                    assert compiled.contexts[0].value == identity
                    assert compiled.contexts[0].to_env == "RUN_ID"
                    assert compiled.run.container.args == [f"echo {identity}"]
                assert parent.contexts[0].value == "parent"

    def test_scheduled_dag_keeps_templates_and_node_fields(self):
        authored = read_polyaxonfile(
            {
                "kind": "component",
                "schedule": {"kind": "interval", "frequency": 60},
                "run": {
                    "kind": "dag",
                    "components": [
                        {
                            "name": "template",
                            "schedule": {"kind": "interval", "frequency": 120},
                            "run": {
                                "kind": "job",
                                "container": {"image": "busybox:1.36"},
                            },
                        }
                    ],
                    "operations": [
                        {"name": "first", "dagRef": "template"},
                        {
                            "name": "second",
                            "dagRef": "template",
                            "dependencies": ["first"],
                            "conditions": "true",
                            "trigger": "all_succeeded",
                            "skipOnUpstreamSkip": False,
                        },
                    ],
                },
            }
        )
        parent = OperationSpecification.compile_operation(authored)
        before = authored.to_dict()

        child = get_op_from_schedule(authored, parent)

        assert child.schedule is None
        assert child.run.to_dict() == parent.run.to_dict()
        assert child.run.components[0].schedule.frequency == timedelta(seconds=120)
        compiled = OperationSpecification.compile_operation(
            read_polyaxonfile(child.to_json())
        )
        compiled = CompiledOperationSpecification.apply_operation_contexts(compiled)
        assert compiled.run.dag["first"].downstream == {"second"}
        assert compiled.run.dag["second"].upstream == {"first"}
        for name in ("first", "second"):
            compiled.run.set_op_component(name)
            node = compiled.run.get_op_spec_by_name(name)
            assert compose_polyaxonfile(node, is_dag_node=True).schedule is None
        second = compiled.run.get_effective_op("second")
        assert second.conditions == "true"
        assert second.trigger == "all_succeeded"
        assert second.skip_on_upstream_skip is False
        assert authored.to_dict() == before
