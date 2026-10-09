from copy import deepcopy
import pytest
from unittest.mock import patch

from clipped.compact.pydantic import ValidationError
from clipped.config.patch_strategy import PatchStrategy
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._flow.run.job import V1Job
from polyaxon._flow.run.service import V1Service
from polyaxon._k8s.k8s_schemas import V1Container
from polyaxon._polyaxonfile import (
    OperationSpecification,
    compose_polyaxonfile,
    read_polyaxonfile,
)
from polyaxon._polyaxonfile.manager import get_op_specification
from polyaxon._polyaxonfile.specs.polyaxonfile import _copy_model_value
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonfileError, PolyaxonSchemaError


_LAYER_COPY_FIELDS = set(V1Polyaxonfile.get_model_fields()) - {"component"}


def count_polyaxonfile_layer_copy_calls(copier):
    return sum(
        isinstance(call.args[0], dict) and set(call.args[0]) == _LAYER_COPY_FIELDS
        for call in copier.call_args_list
    )


@pytest.mark.polyaxonfile_mark
class TestSharedComposition(BaseTestCase):
    def test_native_fields_and_run_patch_follow_each_strategy(self):
        source = {
            "component": {
                "queue": "base",
                "inputs": [{"name": "count", "type": "int"}],
                "outputs": [{"name": "accuracy", "type": "float"}],
                "params": {"count": 1, "base": True},
                "run": {
                    "kind": "job",
                    "connections": ["base"],
                    "container": {"image": "base:v1", "command": ["sh", "-c"]},
                },
            },
            "queue": "local",
            "inputs": [{"name": "message", "type": "str"}],
            "outputs": [{"name": "loss", "type": "float"}],
            "params": {"count": 3, "local": True},
            "run": {
                "kind": "job",
                "connections": ["local"],
                "container": {"image": "local:v2"},
            },
            "runPatch": {
                "connections": ["patch"],
                "container": {"image": "final:v3", "args": ["echo hello"]},
            },
        }
        expected = {
            PatchStrategy.POST_MERGE: {
                "queue": "local",
                "inputs": ["count", "message"],
                "outputs": ["accuracy", "loss"],
                "params": {"count": 3, "base": True, "local": True},
                "connections": ["base", "local", "patch"],
                "image": "final:v3",
            },
            PatchStrategy.PRE_MERGE: {
                "queue": "base",
                "inputs": ["message", "count"],
                "outputs": ["loss", "accuracy"],
                "params": {"count": 1, "base": True, "local": True},
                "connections": ["patch", "local", "base"],
                "image": "base:v1",
            },
            PatchStrategy.REPLACE: {
                "queue": "local",
                "inputs": ["message"],
                "outputs": ["loss"],
                "params": {"count": 3, "local": True},
                "connections": ["patch"],
                "image": "final:v3",
            },
            PatchStrategy.ISNULL: {
                "queue": "base",
                "inputs": ["count"],
                "outputs": ["accuracy"],
                "params": {"count": 1, "base": True},
                "connections": ["base"],
                "image": "base:v1",
            },
        }
        for strategy in (None, *PatchStrategy):
            with self.subTest(strategy=strategy):
                authored = deepcopy(source)
                if strategy:
                    authored["patchStrategy"] = strategy
                before = deepcopy(authored)

                result = compose_polyaxonfile(authored)

                want = expected[strategy or PatchStrategy.POST_MERGE]
                assert result.queue == want["queue"]
                assert [io.name for io in result.inputs] == want["inputs"]
                assert [io.name for io in result.outputs] == want["outputs"]
                assert {k: p.value for k, p in result.params.items()} == want["params"]
                assert result.run.connections == want["connections"]
                assert result.run.container.image == want["image"]
                assert result.run.container.command == ["sh", "-c"]
                assert result.run.container.args == ["echo hello"]
                assert authored == before

    def test_legacy_wrapper_has_fixed_results_across_entry_points(self):
        source = {
            "kind": "operation",
            "component": {
                "kind": "component",
                "strictParams": True,
                "queue": "base",
                "tags": ["base"],
                "inputs": [{"name": "count", "type": "int"}],
                "run": {
                    "kind": "job",
                    "connections": ["base"],
                    "container": {"image": "base:v1", "command": ["sh", "-c"]},
                },
            },
            "strictParams": False,
            "queue": "local",
            "tags": ["local"],
            "params": {"count": 3},
            "runPatch": {
                "connections": ["patch"],
                "container": {"image": "final:v3", "args": ["echo hello"]},
            },
        }
        expected = {
            PatchStrategy.POST_MERGE: {
                "queue": "local",
                "tags": ["base", "local"],
                "connections": ["base", "patch"],
                "image": "final:v3",
            },
            PatchStrategy.PRE_MERGE: {
                "queue": "base",
                "tags": ["local", "base"],
                "connections": ["patch", "base"],
                "image": "base:v1",
            },
            PatchStrategy.REPLACE: {
                "queue": "local",
                "tags": ["local"],
                "connections": ["patch"],
                "image": "final:v3",
            },
            PatchStrategy.ISNULL: {
                "queue": "base",
                "tags": ["base"],
                "connections": ["base"],
                "image": "base:v1",
            },
        }
        for strategy, want in expected.items():
            with self.subTest(strategy=strategy):
                authored = {**source, "patchStrategy": strategy}
                compiled = OperationSpecification.compile_operation(
                    OperationSpecification.read(deepcopy(authored))
                )

                result = compose_polyaxonfile(authored)

                for config in (result, compiled):
                    assert config.run.to_dict() == {
                        "kind": "job",
                        "connections": want["connections"],
                        "container": {
                            "image": want["image"],
                            "command": ["sh", "-c"],
                            "args": ["echo hello"],
                        },
                    }
                    assert [io.to_dict() for io in config.inputs] == [
                        {"name": "count", "type": "int"}
                    ]
                    assert config.queue == want["queue"]
                    assert config.tags == want["tags"]
                    assert config.strict_params is True

    def test_partial_run_inherits_kind_from_embedded_or_resolved_base(self):
        references = (
            {},
            {"hubRef": "train:v1"},
            {"pathRef": "./train.yaml"},
            {"urlRef": "https://example.com/train.yaml"},
            {"dagRef": "train"},
        )
        for kind, runtime in (("job", V1Job), ("service", V1Service)):
            for reference in references:
                with self.subTest(kind=kind, reference=reference):
                    source = {
                        **reference,
                        "component": {
                            "params": {"count": 1},
                            "run": {
                                "kind": kind,
                                "container": {"image": "base:v1"},
                            },
                        },
                        "params": {"count": 3},
                        "run": {"container": {"image": "local:v2"}},
                    }

                    result = compose_polyaxonfile(source)

                    assert type(result.run) is runtime
                    assert result.run.container.image == "local:v2"
                    assert result.params["count"].value == 3
                    assert "kind" not in source["run"]
                    assert result.component is None
                    assert result.hub_ref is None
                    assert result.path_ref is None
                    assert result.url_ref is None
                    assert result.dag_ref is None

    def test_changing_runtime_kind_replaces_the_runtime(self):
        job = {"kind": "job", "container": {"image": "job:v1"}}
        service = {
            "kind": "service",
            "ports": [8080],
            "container": {"image": "service:v1"},
        }
        for base, local in ((job, service), (service, job)):
            for strategy in PatchStrategy:
                with self.subTest(base=base["kind"], strategy=strategy):
                    result = compose_polyaxonfile(
                        {
                            "component": {"run": base},
                            "run": local,
                            "patchStrategy": strategy,
                        }
                    )

                    want = (
                        local
                        if strategy in (PatchStrategy.POST_MERGE, PatchStrategy.REPLACE)
                        else base
                    )
                    assert result.run.to_dict() == want

    def test_run_patch_is_validated_against_the_composed_runtime(self):
        source = {
            "component": {
                "run": {"kind": "job", "container": {"image": "base:v1"}},
            },
            "run": {"kind": "service", "container": {"image": "service:v2"}},
            "runPatch": {"ports": [8080]},
        }

        result = compose_polyaxonfile(source)

        assert isinstance(result.run, V1Service)
        assert result.run.ports == [8080]
        with self.assertRaises(ValidationError):
            compose_polyaxonfile({**source, "patchStrategy": "pre_merge"})

    def test_each_nested_source_uses_its_own_strategy(self):
        source = {
            "component": {
                "component": {
                    "params": {"count": 1},
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                    "runPatch": {"container": {"image": "inner:v2"}},
                },
                "patchStrategy": "pre_merge",
                "params": {"count": 2},
                "run": {"container": {"image": "middle:v3"}},
                "runPatch": {"container": {"image": "middle-patch:v4"}},
            },
            "params": {"count": 3},
            "run": {"container": {"image": "outer:v5"}},
            "runPatch": {"container": {"image": "final:v6"}},
        }
        middle = compose_polyaxonfile(source["component"])
        assert middle.params["count"].value == 1
        assert middle.run.container.image == "inner:v2"

        without_patch = {k: v for k, v in source.items() if k != "runPatch"}
        outer = compose_polyaxonfile(without_patch)
        assert outer.params["count"].value == 3
        assert outer.run.container.image == "outer:v5"

        result = compose_polyaxonfile(source)
        assert result.params["count"].value == 3
        assert result.run.container.image == "final:v6"
        assert result.run_patch is None
        assert result.patch_strategy is None
        assert compose_polyaxonfile(result).to_dict() == result.to_dict()

    def test_nested_sources_are_read_once_and_copied_once_per_layer(self):
        for depth in (1, 4, 8):
            source = {"run": {"kind": "job", "container": {"image": "base:v1"}}}
            for _ in range(depth - 1):
                source = {"component": source, "params": {"count": 3}}
            for authored in (source, read_polyaxonfile(source)):
                with self.subTest(
                    depth=depth, model=isinstance(authored, V1Polyaxonfile)
                ):
                    before = deepcopy(authored)
                    with (
                        patch(
                            "polyaxon._polyaxonfile.specs.polyaxonfile.read_polyaxonfile",
                            wraps=read_polyaxonfile,
                        ) as reader,
                        patch(
                            "polyaxon._polyaxonfile.specs.polyaxonfile._copy_model_value",
                            wraps=_copy_model_value,
                        ) as copier,
                    ):
                        result = compose_polyaxonfile(authored)

                    if isinstance(authored, V1Polyaxonfile):
                        reader.assert_not_called()
                    else:
                        reader.assert_called_once_with(authored)
                    assert count_polyaxonfile_layer_copy_calls(copier) == depth
                    assert result.run.container.image == "base:v1"
                    if depth > 1:
                        assert result.params["count"].value == 3
                    assert authored == before

    def test_atomic_outer_layer_is_read_only_and_does_not_need_a_copy(self):
        source = read_polyaxonfile(
            {
                "component": {
                    "queue": "base",
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                },
                "queue": None,
                "strictParams": False,
            }
        )
        before = deepcopy(source)
        with patch(
            "polyaxon._polyaxonfile.specs.polyaxonfile._copy_model_value",
            wraps=_copy_model_value,
        ) as copier:
            result = compose_polyaxonfile(source)

        assert count_polyaxonfile_layer_copy_calls(copier) == 1
        assert result.queue is None
        assert result.strict_params is False
        result.run.container.image = "changed:v2"
        assert source == before
        assert source.component.run.container.image == "base:v1"
        assert source.model_fields_set == {"component", "queue", "strict_params"}

    def test_composition_options_only_apply_to_the_outer_layer(self):
        source = {
            "component": {
                "component": {
                    "schedule": {"kind": "interval", "frequency": 60},
                    "run": {
                        "kind": "job",
                        "connections": ["base"],
                        "container": {"image": "base:v1"},
                    },
                    "runPatch": {
                        "connections": ["inner"],
                        "container": {"image": "inner:v2"},
                    },
                },
                "patchStrategy": "pre_merge",
                "run": {"container": {"image": "middle:v3"}},
            },
            "name": "node",
            "dependencies": ["prepare"],
            "runPatch": {
                "connections": ["outer"],
                "container": {"image": "outer:v4"},
            },
        }
        before = deepcopy(source)

        result = compose_polyaxonfile(
            source, run_patch_strategy=PatchStrategy.PRE_MERGE, is_dag_node=True
        )

        assert result.run.container.image == "inner:v2"
        assert result.run.connections == ["outer", "base", "inner"]
        assert result.schedule is None
        assert result.name == "node"
        assert result.dependencies == ["prepare"]
        assert source == before

    def test_python_layers_sharing_runtime_objects_remain_independent(self):
        for shared_field in ("run", "container"):
            with self.subTest(shared_field=shared_field):
                base = V1Polyaxonfile(
                    run=V1Job(container=V1Container(image="outer:v1")),
                    run_patch={"container": {"image": "inner:v2"}},
                )
                outer_run = (
                    base.run
                    if shared_field == "run"
                    else V1Job(container=base.run.container)
                )
                source = V1Polyaxonfile.model_construct(component=base, run=outer_run)
                assert source.run.container is source.component.run.container
                if shared_field == "run":
                    assert source.run is source.component.run
                before = deepcopy(source)

                result = compose_polyaxonfile(source)

                assert result.run.container.image == "outer:v1"
                assert source == before
                result.run.container.image = "changed:v3"
                assert source.run.container.image == "outer:v1"
                assert source.component.run.container.image == "outer:v1"
                assert source.component.run_patch == {
                    "container": {"image": "inner:v2"}
                }

    def test_strict_base_cannot_be_relaxed_by_local_fields(self):
        for base, local, expected in (
            (None, None, False),
            (None, False, False),
            (False, False, False),
            (None, True, True),
            (True, None, True),
            (True, False, True),
            (False, True, True),
            (True, True, True),
        ):
            for strategy in PatchStrategy:
                with self.subTest(base=base, local=local, strategy=strategy):
                    result = compose_polyaxonfile(
                        {
                            "component": {
                                "strictParams": base,
                                "params": {
                                    "message": {
                                        "value": "hello",
                                        "contextOnly": True,
                                        "toEnv": "MESSAGE",
                                    }
                                },
                                "run": {"kind": "job"},
                            },
                            "strictParams": local,
                            "patchStrategy": strategy,
                        }
                    )

                    assert result.strict_params is expected
                    assert result.params["message"].context_only is True
                    assert result.params["message"].to_env == "MESSAGE"

    def test_param_override_replaces_the_param_definition(self):
        result = compose_polyaxonfile(
            {
                "component": {
                    "params": {
                        "message": {
                            "value": "hello",
                            "contextOnly": True,
                            "toEnv": "MESSAGE",
                        }
                    },
                },
                "params": {"message": "goodbye"},
            }
        )

        assert result.params["message"].to_dict() == {"value": "goodbye"}

    def test_workflow_fields_are_inherited_and_presets_stay_unresolved(self):
        base = {
            "params": {"epochs": 3},
            "matrix": {
                "kind": "grid",
                "params": {"seed": {"kind": "choice", "value": [1, 2]}},
            },
            "schedule": {"kind": "cron", "cron": "0 * * * *", "maxRuns": 5},
            "presets": ["base-preset"],
            "run": {"kind": "job", "container": {"image": "trainer:v1"}},
        }
        inherited = compose_polyaxonfile({"hubRef": "train:v1", "component": base})
        assert inherited.params["epochs"].value == 3
        assert inherited.matrix.params["seed"].value == [1, 2]
        assert inherited.schedule.cron == "0 * * * *"
        assert inherited.presets == ["base-preset"]

        result = compose_polyaxonfile(
            {
                "component": base,
                "params": {"epochs": 5},
                "matrix": {
                    "kind": "grid",
                    "concurrency": 2,
                    "params": {"lr": {"kind": "choice", "value": [0.1, 0.01]}},
                },
                "schedule": {"kind": "cron", "cron": "0 0 * * *"},
                "presets": ["local-preset"],
            }
        )

        assert result.params["epochs"].value == 5
        assert result.matrix.params["seed"].value == [1, 2]
        assert result.matrix.params["lr"].value == [0.1, 0.01]
        assert result.matrix.concurrency == 2
        assert result.schedule.cron == "0 0 * * *"
        assert result.schedule.max_runs == 5
        assert result.presets == ["base-preset", "local-preset"]

    def test_omitted_null_and_empty_native_fields_keep_existing_patch_rules(self):
        base = {
            "queue": "base",
            "isApproved": True,
            "inputs": [{"name": "count", "type": "int"}],
            "params": {"count": 1},
            "run": {"kind": "job", "container": {"image": "base:v1"}},
        }
        for strategy in PatchStrategy:
            for local in ({}, {"queue": None, "isApproved": False, "run": None}):
                with self.subTest(strategy=strategy, local=local):
                    result = compose_polyaxonfile(
                        {"component": base, "patchStrategy": strategy, **local}
                    )
                    clears = bool(local) and strategy in (
                        PatchStrategy.POST_MERGE,
                        PatchStrategy.REPLACE,
                    )
                    assert result.queue == (None if clears else "base")
                    assert result.is_approved is (not clears)
                    if clears:
                        assert result.run is None
                    else:
                        assert result.run.container.image == "base:v1"
                    assert result.params["count"].value == 1

            empty = compose_polyaxonfile(
                {
                    "component": base,
                    "patchStrategy": strategy,
                    "inputs": [],
                    "params": {},
                    "run": {},
                }
            )
            assert empty.run.container.image == "base:v1"
            if strategy == PatchStrategy.REPLACE:
                assert empty.inputs == []
                assert empty.params == {}
            else:
                assert empty.inputs[0].name == "count"
                assert empty.params["count"].value == 1

    def test_operation_conversion_preserves_omitted_empty_and_null_run(self):
        base = {
            "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
        }
        for kind in (None, "component", "operation"):
            for strategy in (None, *PatchStrategy):
                for local in ({}, {"run": {}}, {"run": None}):
                    with self.subTest(kind=kind, strategy=strategy, local=local):
                        source = {"component": base, **local}
                        if kind:
                            source["kind"] = kind
                        if strategy:
                            source["patchStrategy"] = strategy
                        converted = get_op_specification(
                            config=read_polyaxonfile(source), validate_params=False
                        )
                        submitted = converted.to_dict(exclude_none=False)
                        authored = (
                            submitted["component"] if kind == "component" else submitted
                        )
                        assert ("run" in authored) == ("run" in local)
                        assert "version" not in submitted
                        if "run" in local and local["run"] is None:
                            assert authored["run"] is None

                        result = read_polyaxonfile(submitted)
                        clears = (
                            "run" in local
                            and local["run"] is None
                            and strategy
                            in (
                                None,
                                PatchStrategy.POST_MERGE,
                                PatchStrategy.REPLACE,
                            )
                        )
                        if clears:
                            with self.assertRaisesRegex(
                                PolyaxonSchemaError, "resolved Polyaxonfile has no run"
                            ):
                                OperationSpecification.compile_operation(result)
                        else:
                            compiled = OperationSpecification.compile_operation(result)
                            assert compiled.run.container.image == "busybox:1.36"
                            if local == {"run": {}}:
                                reloaded = read_polyaxonfile(converted.to_json())
                                assert (
                                    OperationSpecification.compile_operation(
                                        reloaded
                                    ).to_dict()
                                    == compiled.to_dict()
                                )

    def test_container_resource_patch_keeps_inherited_gpu(self):
        result = compose_polyaxonfile(
            {
                "component": {
                    "run": {
                        "kind": "job",
                        "container": {
                            "image": "trainer:v1",
                            "resources": {
                                "requests": {"cpu": "2"},
                                "limits": {"nvidia.com/gpu": 1, "memory": "4Gi"},
                            },
                        },
                    },
                },
                "run": {"container": {"resources": {"requests": {"cpu": "4"}}}},
                "runPatch": {"container": {"resources": {"limits": {"cpu": "8"}}}},
            }
        )

        assert result.run.container.resources == {
            "requests": {"cpu": "4"},
            "limits": {"cpu": "8", "nvidia.com/gpu": 1, "memory": "4Gi"},
        }

    def test_distributed_run_patch_uses_existing_replica_behavior(self):
        for field in ("run", "runPatch"):
            with self.subTest(field=field):
                result = compose_polyaxonfile(
                    {
                        "component": {
                            "run": {
                                "kind": "pytorchjob",
                                "worker": {
                                    "replicas": 2,
                                    "container": {"image": "base:v1"},
                                },
                            },
                        },
                        field: {"container": {"image": "final:v2"}},
                    },
                )

                assert result.run.worker.replicas == 2
                assert result.run.worker.container.image == "final:v2"
                assert result.run.master is None

    def test_model_input_keeps_nested_field_presence_and_is_not_modified(self):
        source = read_polyaxonfile(
            {
                "component": {
                    "component": {
                        "queue": "base",
                        "run": {"kind": "job", "container": {"image": "base:v1"}},
                    },
                    "queue": None,
                },
                "params": {"count": 3},
                "runPatch": {"container": {"image": "final:v2"}},
            }
        )
        before = deepcopy(source)

        result = compose_polyaxonfile(source)

        assert result.queue is None
        assert result.run.container.image == "final:v2"
        assert source == before
        assert "queue" in source.component.model_fields_set
        assert source.component.component.run.container.image == "base:v1"
        result.params["count"].value = 4
        result.run.container.image = "changed:v3"
        assert source.params["count"].value == 3
        assert source.run_patch == {"container": {"image": "final:v2"}}
        assert source.component.component.run.container.image == "base:v1"

    def test_model_values_and_field_presence_are_preserved_separately(self):
        source = V1Polyaxonfile.model_construct(
            _fields_set={"component", "queue"},
            component=read_polyaxonfile(
                {
                    "queue": "base",
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                }
            ),
            queue=None,
            strict_params=True,
            version=1.1,
            run_patch={"container": {"image": "final:v2"}},
        )
        before = deepcopy(source)

        result = compose_polyaxonfile(source)

        assert result.queue is None
        assert result.strict_params is True
        assert result.version == 1.1
        assert result.run.container.image == "final:v2"
        assert source.model_fields_set == {"component", "queue"}
        assert source == before

    def test_unresolved_references_are_rejected(self):
        for field, ref in (
            ("hubRef", "train:v1"),
            ("pathRef", "./train.yaml"),
            ("urlRef", "https://example.com/train.yaml"),
            ("dagRef", "train"),
        ):
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(PolyaxonfileError, "Collect.*reference"),
            ):
                compose_polyaxonfile({field: ref, "params": {"count": 3}})

    def test_invalid_fields_and_runtime_patches_are_rejected(self):
        for local in (
            {"unknown": True},
            {"run": {"kind": "unknown"}},
            {"run": {"kind": None}},
            {"run": {"ports": [8080]}},
            {"runPatch": {"ports": [8080]}},
        ):
            with self.subTest(local=local), self.assertRaises(ValidationError):
                compose_polyaxonfile({"component": {"run": {"kind": "job"}}, **local})

        with self.assertRaisesRegex(ValidationError, "run.kind must be provided"):
            compose_polyaxonfile({"run": {"container": {"image": "busybox:1.36"}}})
        with self.assertRaisesRegex(PolyaxonfileError, "runPatch requires"):
            compose_polyaxonfile({"runPatch": {"container": {"image": "busybox:1.36"}}})
