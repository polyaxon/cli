from copy import deepcopy
import pytest
import subprocess
import sys

from clipped.compact.pydantic import ValidationError
from clipped.config.patch_strategy import PatchStrategy
from polyaxon._flow.component.component import V1Component
from polyaxon._flow.operations.compiled_operation import V1CompiledOperation
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    ComponentSpecification,
    OperationSpecification,
    compose_polyaxonfile,
    get_op_specification,
    get_specification,
    read_polyaxonfile,
)
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import (
    PolyaxonfileError,
    PolyaxonSchemaError,
    PolyaxonValidationError,
)


@pytest.mark.polyaxonfile_mark
class TestSharedCompilation(BaseTestCase):
    def test_direct_files_and_legacy_wrapper_compile_and_render_the_same_job(self):
        native = {
            "inputs": [{"name": "count", "type": "int"}],
            "outputs": [{"name": "result", "type": "str", "value": "done"}],
            "run": {
                "kind": "job",
                "container": {
                    "image": "busybox:1.36",
                    "command": ["sh", "-c"],
                    "args": ["echo 'count={{ count }} message={{ message }}'"],
                    "resources": {
                        "requests": {"cpu": "500m"},
                        "limits": {"nvidia.com/gpu": 1},
                    },
                },
            },
        }
        params = {
            "count": 3,
            "message": {"value": "hello", "contextOnly": True},
            "extra": "available",
        }
        sources = [
            {**native, "params": params},
            {"kind": "component", **native, "params": params},
            {"kind": "operation", **native, "params": params},
            {"kind": "operation", "component": native, "params": params},
        ]
        expected = {
            "kind": "compiled_operation",
            "strictParams": False,
            "contexts": [{"name": "message"}],
            **native,
            "outputs": [
                {"name": "result", "type": "str", "value": "done", "isOptional": True}
            ],
        }
        for source in sources:
            with self.subTest(source=source):
                authored = get_specification(deepcopy(source))
                before = authored.to_dict()

                compiled = OperationSpecification.compile_operation(authored)

                assert type(compiled) is V1CompiledOperation
                assert not isinstance(compiled, V1Polyaxonfile)
                assert compiled.to_dict() == expected
                assert authored.to_dict() == before
                effective = compose_polyaxonfile(authored)
                compiled.apply_params(effective.params)
                compiled = CompiledOperationSpecification.apply_operation_contexts(
                    compiled
                )
                assert compiled.inputs[0].value == 3
                assert {io.name: io.value for io in compiled.contexts} == {
                    "message": "hello",
                    "extra": "available",
                }
                compiled = CompiledOperationSpecification.apply_runtime_contexts(
                    compiled
                )
                assert compiled.run.container.args == ["echo 'count=3 message=hello'"]
                assert authored.to_dict() == before

    def test_invocation_fields_on_a_component_reach_the_compiled_operation(self):
        source = {
            "kind": "component",
            "inputs": [{"name": "count", "type": "int"}],
            "params": {
                "count": 3,
                "message": {
                    "value": "hello",
                    "contextOnly": True,
                    "toEnv": "MESSAGE",
                },
            },
            "matrix": {
                "kind": "grid",
                "params": {"seed": {"kind": "choice", "value": [1, 2]}},
            },
            "schedule": {"kind": "cron", "cron": "0 * * * *"},
            "joins": [
                {
                    "query": "status:succeeded",
                    "params": {
                        "scores": {"value": "outputs.score", "contextOnly": True}
                    },
                }
            ],
            "events": [{"kinds": ["run_status_succeeded"], "ref": "train"}],
            "dependencies": ["prepare"],
            "conditions": "{{ count > 0 }}",
            "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
        }
        component = ComponentSpecification.read(source)
        for authored in (component, V1Operation(component=component)):
            with self.subTest(kind=authored.kind):
                compiled = OperationSpecification.compile_operation(authored)

                assert compiled.inputs == component.inputs
                assert compiled.matrix == component.matrix
                assert compiled.schedule == component.schedule
                assert compiled.joins == component.joins
                assert compiled.events == component.events
                assert compiled.dependencies == ["prepare"]
                assert compiled.conditions == "{{ count > 0 }}"
                assert compiled.contexts[0].name == "message"
                assert compiled.contexts[0].to_env == "MESSAGE"
                assert compiled.contexts[1].name == "scores"
                assert compiled.contexts[1].is_list is True

    def test_native_run_then_run_patch_follow_each_strategy(self):
        source = {
            "component": {
                "queue": "base",
                "params": {"count": 1},
                "run": {
                    "kind": "job",
                    "container": {
                        "image": "base:v1",
                        "command": ["sh", "-c"],
                        "resources": {"limits": {"nvidia.com/gpu": 1}},
                    },
                },
            },
            "queue": "local",
            "params": {"count": 3},
            "run": {"container": {"image": "local:v2"}},
            "runPatch": {"container": {"image": "final:v3", "args": ["echo hello"]}},
        }
        for model in (V1Polyaxonfile, V1Component, V1Operation):
            for strategy in PatchStrategy:
                with self.subTest(model=model, strategy=strategy):
                    authored = model.from_dict(
                        {**deepcopy(source), "patchStrategy": strategy}
                    )
                    before = authored.to_dict()

                    compiled = OperationSpecification.compile_operation(authored)

                    local_wins = strategy in (
                        PatchStrategy.POST_MERGE,
                        PatchStrategy.REPLACE,
                    )
                    assert compiled.queue == ("local" if local_wins else "base")
                    assert compiled.run.container.image == (
                        "final:v3" if local_wins else "base:v1"
                    )
                    assert compiled.run.container.command == ["sh", "-c"]
                    assert compiled.run.container.args == ["echo hello"]
                    assert compiled.run.container.resources == {
                        "limits": {"nvidia.com/gpu": 1}
                    }
                    assert authored.to_dict() == before

    def test_run_patch_validation_uses_the_final_runtime_kind(self):
        source = {
            "component": {"run": {"kind": "job", "container": {"image": "base:v1"}}},
            "run": {"kind": "service", "container": {"image": "service:v2"}},
            "runPatch": {"ports": [8080]},
        }
        for model in (V1Component, V1Operation):
            authored = model.from_dict(deepcopy(source))
            compiled = OperationSpecification.compile_operation(authored)
            assert compiled.run.kind == "service"
            assert compiled.run.ports == [8080]
            assert compiled.run.container.image == "service:v2"

            authored.patch_strategy = PatchStrategy.PRE_MERGE
            with self.assertRaises(ValidationError):
                OperationSpecification.compile_operation(authored)

    def test_restart_override_strategy_only_changes_run_patch_application(self):
        source = {
            "kind": "operation",
            "patchStrategy": "pre_merge",
            "component": {
                "queue": "base",
                "run": {"kind": "job", "container": {"image": "base:v1"}},
            },
            "queue": "local",
            "run": {"kind": "job", "container": {"image": "local:v2"}},
            "runPatch": {"container": {"image": "patch:v3"}},
        }
        override = {
            "patchStrategy": "post_merge",
            "queue": "override",
            "params": {"count": 5},
            "runPatch": {"container": {"image": "override:v4"}},
        }
        for use_override in (False, True):
            authored = OperationSpecification.read(deepcopy(source))
            compiled = OperationSpecification.compile_operation(
                authored,
                override=deepcopy(override),
                use_override_patch_strategy=use_override,
            )
            assert compiled.queue == "base"
            assert compiled.run.container.image == (
                "override:v4" if use_override else "base:v1"
            )
            assert authored.patch_strategy == "pre_merge"
            # Existing callers read override params from the operation after compilation.
            assert authored.params["count"].value == 5
            assert authored.component.run.container.image == "base:v1"

    def test_component_can_receive_an_operation_shaped_override(self):
        component = ComponentSpecification.read(
            {"run": {"kind": "job", "container": {"image": "base:v1"}}}
        )
        compiled = OperationSpecification.compile_operation(
            component,
            override={
                "kind": "operation",
                "run": {"kind": "job", "container": {"image": "override:v2"}},
            },
        )
        assert component.kind == "component"
        assert compiled.run.container.image == "override:v2"

    def test_native_override_inherits_the_collected_runtime_kind(self):
        for runtime in ("job", "service"):
            for kind in (None, "component", "operation"):
                with self.subTest(runtime=runtime, kind=kind):
                    source = {
                        "kind": "component",
                        "component": {
                            "run": {
                                "kind": runtime,
                                "container": {
                                    "image": "base:v1",
                                    "command": ["sh", "-c"],
                                },
                            }
                        },
                    }
                    override = {"run": {"container": {"image": "override:v2"}}}
                    if kind:
                        override["kind"] = kind
                    before = deepcopy(override)

                    compiled = OperationSpecification.compile_operation(
                        read_polyaxonfile(source), override=override
                    )

                    assert compiled.run.kind == runtime
                    assert compiled.run.container.image == "override:v2"
                    assert compiled.run.container.command == ["sh", "-c"]
                    assert override == before

    def test_override_reading_keeps_existing_input_forms(self):
        values = {
            "params": {"count": 5},
            "run": {"kind": "service", "container": {"image": "override:v2"}},
        }
        for override in (
            V1Operation.from_dict(values),
            V1Component.from_dict(values),
            V1Operation.from_dict(values).to_json(),
            [{"params": {"count": 3}}, values],
        ):
            with self.subTest(override=override):
                authored = read_polyaxonfile(
                    {"run": {"kind": "service", "container": {"image": "base:v1"}}}
                )

                compiled = OperationSpecification.compile_operation(
                    authored, override=override
                )

                assert compiled.run.kind == "service"
                assert compiled.run.container.image == "override:v2"
                assert authored.params["count"].value == 5

    def test_strict_component_stays_strict_and_context_only_still_bypasses_it(self):
        for model in (V1Polyaxonfile, V1Component, V1Operation):
            authored = model.from_dict(
                {
                    "strictParams": False,
                    "component": {
                        "strictParams": True,
                        "params": {"message": {"value": "hello", "contextOnly": True}},
                        "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
                    },
                    "params": {"extra": 1},
                }
            )
            compiled = OperationSpecification.compile_operation(authored)
            params = compose_polyaxonfile(authored).params
            assert compiled.strict_params is True
            with self.assertRaisesRegex(PolyaxonValidationError, "undeclared param"):
                compiled.validate_params(params=params)
            params.pop("extra")
            assert [p.name for p in compiled.validate_params(params=params)] == [
                "message"
            ]

    def test_missing_runtime_is_rejected_at_compilation(self):
        for source in ({}, {"params": {"count": 3}}, {"component": {"inputs": []}}):
            for model in (V1Polyaxonfile, V1Component, V1Operation):
                with self.subTest(source=source, model=model):
                    authored = model.from_dict(source)
                    with self.assertRaisesRegex(PolyaxonSchemaError, "has no run"):
                        OperationSpecification.compile_operation(authored)

    def test_reference_must_be_collected_even_when_a_local_run_is_present(self):
        for ref in ("hubRef", "pathRef", "urlRef", "dagRef"):
            authored = read_polyaxonfile(
                {
                    ref: "base",
                    "run": {"kind": "job", "container": {"image": "local:v1"}},
                }
            )
            with self.assertRaisesRegex(
                PolyaxonfileError, "Collect the Polyaxonfile reference"
            ):
                OperationSpecification.compile_operation(authored)

    def test_authored_fields_are_removed_and_legacy_version_precedence_is_preserved(
        self,
    ):
        authored = OperationSpecification.read(
            {
                "version": 1.1,
                "hubRef": "train:v1",
                "component": {
                    "version": 0.4,
                    "template": {"enabled": False},
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                },
                "params": {"count": 3},
                "patchStrategy": "post_merge",
                "runPatch": {"container": {"image": "local:v2"}},
            }
        )
        before = authored.to_dict()
        for _ in range(2):
            compiled = OperationSpecification.compile_operation(authored)
            assert compiled.to_dict() == {
                "kind": "compiled_operation",
                "version": 0.4,
                "strictParams": False,
                "contexts": [],
                "run": {"kind": "job", "container": {"image": "local:v2"}},
            }
            assert get_specification(compiled.to_dict()).to_dict() == compiled.to_dict()
            assert authored.to_dict() == before

    def test_submission_validation_uses_params_from_the_component(self):
        component = ComponentSpecification.read(
            {
                "inputs": [{"name": "count", "type": "int"}],
                "params": {"count": 3},
                "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
            }
        )
        operation = get_op_specification(config=component)
        assert operation.component.params["count"].value == 3
        assert operation.params is None
        compiled = OperationSpecification.compile_operation(operation)
        compiled.apply_params(compose_polyaxonfile(operation).params)
        assert compiled.inputs[0].value == 3

    def test_public_model_imports_resolve_recursive_dags_without_importing_schemas(
        self,
    ):
        source = {
            "run": {
                "kind": "dag",
                "operations": [
                    {
                        "name": "train",
                        "component": {
                            "run": {
                                "kind": "job",
                                "container": {"image": "busybox:1.36"},
                            }
                        },
                    }
                ],
            }
        }
        for module, name in (
            ("polyaxon._flow.polyaxonfile", "V1Polyaxonfile"),
            ("polyaxon._flow.component.component", "V1Component"),
            ("polyaxon._flow.operations.operation", "V1Operation"),
        ):
            with self.subTest(module=module):
                script = f"""
from {module} import {name}
source = {source!r}
config = {name}.from_dict(source)
assert config.to_dict() == source
assert {name}.read(config.to_json()).to_dict() == source
assert config.run.operations[0].component.kind == "component"
"""
                result = subprocess.run(
                    [sys.executable, "-c", script], capture_output=True, text=True
                )
                assert result.returncode == 0, result.stdout + result.stderr
