from copy import deepcopy
from itertools import product
from pathlib import Path
import pytest
from tempfile import TemporaryDirectory
import yaml

from clipped.compact.pydantic import ValidationError
from clipped.config.patch_strategy import PatchStrategy
from polyaxon._flow.init import V1Init
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
    compose_polyaxonfile,
    get_op_specification,
    patch_polyaxonfile,
    read_polyaxonfile,
)
from polyaxon._polyaxonfile.check import collect_references
from polyaxon._schemas.types import V1GitType
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonSchemaError, PolyaxonValidationError


@pytest.mark.polyaxonfile_mark
class TestSharedFilePatches(BaseTestCase):
    def test_kindless_run_layers_keep_file_strategy_separate_from_component(self):
        source = read_polyaxonfile(
            {
                "patchStrategy": "pre_merge",
                "component": {
                    "run": {
                        "kind": "job",
                        "container": {"image": "base:v1", "command": ["sh", "-c"]},
                    },
                },
                "run": {"container": {"image": "first:v2"}},
            }
        )
        before = source.to_dict()
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
                overlay = {
                    "patchStrategy": strategy,
                    "run": {"container": {"image": "second:v3"}},
                }

                merged = patch_polyaxonfile(source, [overlay])
                compiled = OperationSpecification.compile_operation(merged)
                overridden = OperationSpecification.compile_operation(
                    source, override=overlay
                )

                local_image = (
                    "second:v3"
                    if strategy in (PatchStrategy.POST_MERGE, PatchStrategy.REPLACE)
                    else "first:v2"
                )
                assert merged.run.to_dict() == {
                    "kind": "job",
                    "container": {"image": local_image},
                }
                assert merged.patch_strategy == "pre_merge"
                assert merged.component.to_dict() == source.component.to_dict()
                assert compiled.run.container.image == "base:v1"
                assert compiled.run.container.command == ["sh", "-c"]
                assert overridden.run.to_dict() == compiled.run.to_dict()
                assert source.to_dict() == before

    def test_kindless_replica_patches_merge_before_legacy_run_patch(self):
        source = read_polyaxonfile(
            {
                "component": {
                    "run": {
                        "kind": "pytorchjob",
                        "worker": {
                            "replicas": 2,
                            "container": {
                                "image": "base:v1",
                                "command": ["sh", "-c"],
                            },
                        },
                    },
                },
                "run": {"container": {"image": "first:v2"}},
                "runPatch": {"container": {"image": "final:v4"}},
            }
        )
        overlay = {"run": {"container": {"image": "second:v3"}}}

        merged = patch_polyaxonfile(source, [overlay])
        compiled = OperationSpecification.compile_operation(merged)
        overridden = OperationSpecification.compile_operation(source, override=overlay)

        assert merged.run.to_dict() == {
            "kind": "pytorchjob",
            "worker": {"container": {"image": "second:v3"}},
        }
        assert merged.run_patch == source.run_patch
        assert compiled.run.worker.replicas == 2
        assert compiled.run.worker.container.image == "final:v4"
        assert compiled.run.worker.container.command == ["sh", "-c"]
        assert compiled.run.master is None
        assert overridden.run.to_dict() == compiled.run.to_dict()

    def test_multiple_files_match_cli_entry_point(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "base.yaml"
            base.write_text(
                "kind: operation\n"
                "component:\n"
                "  run: {kind: job, container: {image: base:v1}}\n"
                "runPatch: {container: {image: initial:v1}}\n"
            )
            first = root / "first.yaml"
            first.write_text(
                "kind: operation\n"
                "patchStrategy: post_merge\n"
                "runPatch: {container: {image: first:v2}}\n"
            )
            second = root / "second.yaml"
            second.write_text(
                "kind: operation\n"
                "patchStrategy: pre_merge\n"
                "runPatch:\n"
                "  container: {image: second:v3}\n"
                "  environment: {annotations: {source: second}}\n"
            )
            overlays = [str(first), str(second)]
            source = read_polyaxonfile(str(base))
            before = deepcopy(source)

            merged = patch_polyaxonfile(source, overlays)
            cli_config = get_op_specification(
                config=OperationSpecification.read(str(base)),
                preset_files=overlays,
                validate_params=False,
            )

        assert merged.to_dict() == cli_config.to_dict()
        assert source == before
        assert merged.component.run.container.image == "base:v1"
        assert merged.run_patch["container"]["image"] == "first:v2"
        assert merged.run_patch["environment"]["annotations"] == {"source": "second"}
        assert merged.patch_strategy is None
        effective = compose_polyaxonfile(merged)
        compiled = OperationSpecification.compile_operation(cli_config)
        assert effective.run.to_dict() == compiled.run.to_dict()
        assert effective.run.container.image == "first:v2"
        assert effective.run.environment.annotations == {"source": "second"}

    def test_each_file_supplies_the_strategy_for_native_fields_and_run_patch(self):
        source = read_polyaxonfile(
            {
                "patchStrategy": "post_merge",
                "queue": "base",
                "inputs": [{"name": "count", "type": "int"}],
                "params": {"count": 1, "base": True},
                "run": {
                    "kind": "job",
                    "connections": ["base"],
                    "container": {"image": "base:v1", "command": ["sh", "-c"]},
                },
                "runPatch": {
                    "container": {"image": "initial:v1", "args": ["first"]},
                },
            }
        )
        expected = {
            "post_merge": {
                "queue": "local",
                "inputs": ["count", "message"],
                "params": {"count": 3, "base": True, "local": True},
                "connections": ["base", "local"],
                "native_image": "local:v2",
                "patch_image": "final:v3",
                "args": ["first", "second"],
            },
            "pre_merge": {
                "queue": "base",
                "inputs": ["message", "count"],
                "params": {"count": 1, "base": True, "local": True},
                "connections": ["local", "base"],
                "native_image": "base:v1",
                "patch_image": "initial:v1",
                "args": ["second", "first"],
            },
            "replace": {
                "queue": "local",
                "inputs": ["message"],
                "params": {"count": 3, "local": True},
                "connections": ["local"],
                "native_image": "local:v2",
                "patch_image": "final:v3",
                "args": ["second"],
            },
            "isnull": {
                "queue": "base",
                "inputs": ["count"],
                "params": {"count": 1, "base": True},
                "connections": ["base"],
                "native_image": "base:v1",
                "patch_image": "initial:v1",
                "args": ["first"],
            },
        }
        with TemporaryDirectory() as directory:
            overlay = Path(directory) / "overlay.yaml"
            for strategy, want in expected.items():
                with self.subTest(strategy=strategy):
                    overlay.write_text(
                        yaml.safe_dump(
                            {
                                "patchStrategy": strategy,
                                "queue": "local",
                                "inputs": [{"name": "message", "type": "str"}],
                                "params": {"count": 3, "local": True},
                                "run": {
                                    "connections": ["local"],
                                    "container": {"image": "local:v2"},
                                },
                                "runPatch": {
                                    "container": {
                                        "image": "final:v3",
                                        "args": ["second"],
                                    },
                                },
                            }
                        )
                    )

                    merged = patch_polyaxonfile(source, [str(overlay)])

                    assert merged.patch_strategy == "post_merge"
                    assert merged.queue == want["queue"]
                    assert [io.name for io in merged.inputs] == want["inputs"]
                    assert {k: p.value for k, p in merged.params.items()} == want[
                        "params"
                    ]
                    assert merged.run.connections == want["connections"]
                    assert merged.run.container.image == want["native_image"]
                    assert merged.run.container.command == ["sh", "-c"]
                    assert merged.run_patch["container"]["image"] == want["patch_image"]
                    assert merged.run_patch["container"]["args"] == want["args"]
                    effective = compose_polyaxonfile(merged)
                    assert effective.run.container.image == want["patch_image"]
                    assert effective.run.container.args == want["args"]

    def test_later_native_run_keeps_retained_run_patch(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "base.yaml"
            base.write_text(
                "run: {kind: job, container: {image: base:v1}}\n"
                "runPatch: {container: {image: final:v3}}\n"
            )
            overlay = root / "overlay.yaml"
            overlay.write_text("run: {container: {image: local:v2}}\n")

            merged = patch_polyaxonfile(read_polyaxonfile(str(base)), [str(overlay)])

        assert merged.run.container.image == "local:v2"
        assert merged.run_patch == {"container": {"image": "final:v3"}}
        stored = read_polyaxonfile(merged.to_json())
        effective = compose_polyaxonfile(stored)
        assert effective.run.container.image == "final:v3"
        assert stored.run.container.image == "local:v2"
        assert stored.run_patch == merged.run_patch

    def test_reference_collection_file_merging_and_composition_keep_source(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "templates").mkdir()
            (root / "templates" / "job.yaml").write_text(
                "kind: component\n"
                "inputs: [{name: count, type: int}]\n"
                "params: {count: 1}\n"
                "run:\n"
                "  kind: job\n"
                "  container:\n"
                "    image: trainer:v1\n"
                "    resources: {limits: {nvidia.com/gpu: 1}}\n"
            )
            base = root / "base.yaml"
            base.write_text("pathRef: ./templates/job.yaml\n")
            first = root / "first.yaml"
            first.write_text(
                "params: {count: 3}\n"
                "run:\n"
                "  container:\n"
                "    image: first:v2\n"
                "    resources: {requests: {cpu: '4'}}\n"
            )
            second = root / "second.yaml"
            second.write_text(
                "params: {count: 5}\nrun: {container: {image: second:v3}}\n"
            )
            source = read_polyaxonfile(str(base))
            collect_references(source, str(base))
            before = deepcopy(source)

            merged = patch_polyaxonfile(source, [str(first), str(second)])
            reversed_files = patch_polyaxonfile(source, [str(second), str(first)])

        assert source == before
        assert merged.path_ref == "./templates/job.yaml"
        assert merged.component.to_dict() == source.component.to_dict()
        assert merged.component.params["count"].value == 1
        assert merged.run.container.image == "second:v3"
        assert merged.params["count"].value == 5
        assert reversed_files.run.container.image == "first:v2"
        assert reversed_files.params["count"].value == 3
        stored = read_polyaxonfile(merged.to_json())
        effective = compose_polyaxonfile(stored)
        assert effective.inputs[0].name == "count"
        assert effective.params["count"].value == 5
        assert effective.run.container.resources == {
            "requests": {"cpu": "4"},
            "limits": {"nvidia.com/gpu": 1},
        }

    def test_dag_file_overlays_keep_reference_context_and_patch_strategy(self):
        expected = {
            "post_merge": ["base", "first", "second"],
            "pre_merge": ["second", "base", "first"],
            "replace": ["second"],
            "isnull": ["base", "first"],
        }
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("base", "first", "second"):
                (root / name).mkdir()
                (root / name / "job.yaml").write_text(
                    "run: {kind: job, container: {image: " + name + ":v1}}\n"
                )
            base = root / "base" / "base.yaml"
            files = [str(root / name / "overlay.yaml") for name in ("first", "second")]
            for field, typed in (("run", True), ("run", False), ("dag", False)):
                section = "run:\n  kind: dag\n" if field == "run" else "dag:\n"
                base.write_text(
                    section + "  operations:\n    - {name: base, pathRef: ./job.yaml}\n"
                )
                source = collect_references(read_polyaxonfile(str(base)), str(base))
                before = deepcopy(source)
                for strategy, names in expected.items():
                    with self.subTest(field=field, typed=typed, strategy=strategy):
                        for name, filename in zip(("first", "second"), files):
                            node = {"name": name, "pathRef": "./job.yaml"}
                            if name == "first":
                                node.update(schedule=None, matrix=None)
                            runtime = {"operations": [node]}
                            if typed:
                                runtime["kind"] = "dag"
                            Path(filename).write_text(
                                yaml.safe_dump(
                                    {
                                        "hubRef": "ignored:v1",
                                        "urlRef": "https://example.com/ignored.yaml",
                                        "pathRef": "./ignored.yaml",
                                        "component": {"pathRef": "./ignored-base.yaml"},
                                        "patchStrategy": (
                                            "post_merge"
                                            if name == "first"
                                            else strategy
                                        ),
                                        field: runtime,
                                    }
                                )
                            )

                        merged = patch_polyaxonfile(source, files)
                        stored = read_polyaxonfile(merged.to_source_json())
                        operations = getattr(stored, field).operations

                        assert [op.name for op in operations] == names
                        assert stored.component is None
                        assert stored.hub_ref is None
                        assert stored.url_ref is None
                        assert stored.path_ref is None
                        assert source == before
                        for op in operations:
                            assert op.path_ref == "./job.yaml"
                            assert op.component.run.container.image == op.name + ":v1"
                            assert op.schedule is None
                            assert op.matrix is None
                            assert ("schedule" in op.model_fields_set) == (
                                op.name == "first"
                            )
                            assert ("matrix" in op.model_fields_set) == (
                                op.name == "first"
                            )

    def test_dag_file_overlays_collect_templates_and_nested_references(self):
        source = read_polyaxonfile({"run": {"kind": "dag"}})
        with TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "nested"
            nested.mkdir()
            (root / "job.yaml").write_text(
                "run: {kind: job, container: {image: outer:v1}}\n"
            )
            (nested / "job.yaml").write_text(
                "run: {kind: job, container: {image: inner:v2}}\n"
            )
            (nested / "dag.yaml").write_text(
                "kind: component\n"
                "run:\n"
                "  kind: dag\n"
                "  operations:\n"
                "    - {name: inner, pathRef: ./job.yaml}\n"
            )
            overlay = root / "overlay.yaml"
            for typed in (True, False):
                with self.subTest(typed=typed):
                    runtime = {
                        "components": [
                            {"name": "template", "pathRef": "./nested/dag.yaml"}
                        ],
                        "operations": [
                            {"name": "from-template", "dagRef": "template"},
                            {"name": "from-file", "pathRef": "./nested/dag.yaml"},
                            {
                                "name": "direct",
                                "run": {
                                    "kind": "dag",
                                    "operations": [
                                        {"name": "inner", "pathRef": "./job.yaml"}
                                    ],
                                },
                            },
                        ],
                    }
                    if typed:
                        runtime["kind"] = "dag"
                    overlay.write_text(yaml.safe_dump({"run": runtime}))

                    merged = patch_polyaxonfile(source, [str(overlay)])
                    stored = read_polyaxonfile(merged.to_source_json())

                    assert stored.run.components[0].component.kind == "component"
                    assert stored.run.operations[0].component is None
                    compiled = OperationSpecification.compile_operation(stored)
                    CompiledOperationSpecification.apply_operation_contexts(compiled)
                    for name in ("from-template", "from-file", "direct"):
                        inner = compiled.run.get_effective_op(name).run.operations[0]
                        assert inner.path_ref == "./job.yaml"
                        assert inner.component.run.container.image == (
                            "outer:v1" if name == "direct" else "inner:v2"
                        )

    def test_dag_file_overlay_reference_errors_include_the_entry_name(self):
        source = read_polyaxonfile({"run": {"kind": "dag"}})
        with TemporaryDirectory() as directory:
            overlay = Path(directory) / "overlay.yaml"
            for typed in (True, False):
                for field in ("components", "operations"):
                    for path, error in (
                        ("./overlay.yaml", "reference cycle"),
                        ("./missing.yaml", "does not exist"),
                    ):
                        with self.subTest(typed=typed, field=field, path=path):
                            runtime = {field: [{"name": "train", "pathRef": path}]}
                            if typed:
                                runtime["kind"] = "dag"
                            overlay.write_text(yaml.safe_dump({"run": runtime}))

                            with self.assertRaisesRegex(
                                PolyaxonSchemaError, "train.*" + error
                            ):
                                patch_polyaxonfile(source, [str(overlay)])

    def test_dag_overlay_input_forms_do_not_mutate_authored_values(self):
        source = read_polyaxonfile({"run": {"kind": "dag"}})
        with TemporaryDirectory() as directory:
            job = Path(directory) / "job.yaml"
            job.write_text("run: {kind: job, container: {image: trainer:v1}}\n")
            for typed in (True, False):
                runtime = {
                    "operations": [
                        {"name": "train", "pathRef": str(job), "schedule": None}
                    ]
                }
                if typed:
                    runtime["kind"] = "dag"
                values = {"run": runtime}
                for overlay in (
                    values,
                    read_polyaxonfile(values, is_preset=True),
                    yaml.safe_dump(values),
                    [{"queue": "default"}, values],
                ):
                    with self.subTest(typed=typed, form=type(overlay)):
                        before = deepcopy((source, overlay))

                        merged = patch_polyaxonfile(source, [overlay])
                        stored = read_polyaxonfile(merged.to_source_json())

                        assert (source, overlay) == before
                        node = stored.run.operations[0]
                        assert node.component.run.container.image == "trainer:v1"
                        assert node.schedule is None
                        assert "schedule" in node.model_fields_set
                        assert "kind" not in node.model_fields_set
                        assert "matrix" not in node.model_fields_set

    def test_overlay_strategy_does_not_replace_composition_strategy_or_source(self):
        source = read_polyaxonfile(
            {
                "version": 1.1,
                "kind": "operation",
                "hubRef": "train:v1",
                "patchStrategy": "pre_merge",
                "component": {
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                },
                "run": {"kind": "job", "container": {"image": "local:v2"}},
            }
        )
        merged = patch_polyaxonfile(
            source,
            [
                {
                    "version": 9.9,
                    "hubRef": "ignored:v1",
                    "pathRef": "ignored.yaml",
                    "component": {
                        "run": {"kind": "job", "container": {"image": "ignored:v1"}},
                    },
                    "patchStrategy": "post_merge",
                    "run": {"container": {"image": "overlay:v3"}},
                }
            ],
        )

        assert merged.version == 1.1
        assert merged.hub_ref == "train:v1"
        assert merged.path_ref is None
        assert merged.is_preset is None
        assert merged.patch_strategy == "pre_merge"
        assert merged.component.to_dict() == source.component.to_dict()
        assert merged.run.container.image == "overlay:v3"
        assert compose_polyaxonfile(merged).run.container.image == "base:v1"

    def test_run_patch_merges_against_runtime_kind_of_each_file(self):
        # Files merge like compilation overrides; a later kind cannot fix earlier patches.
        source = read_polyaxonfile(
            {
                "run": {"kind": "job", "container": {"image": "base:v1"}},
                "runPatch": {"ports": [8080]},
            }
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.yaml"
            first.write_text(
                "runPatch: {environment: {annotations: {source: first}}}\n"
            )
            second = root / "second.yaml"
            second.write_text("run: {kind: service, container: {image: server:v2}}\n")

            with pytest.raises(ValidationError, match="ports"):
                patch_polyaxonfile(source, [str(first), str(second)])

        assert source.run.kind == "job"
        assert source.run_patch == {"ports": [8080]}

    def test_partial_run_uses_runtime_kind_after_prior_file_merges(self):
        source = read_polyaxonfile(
            {
                "run": {
                    "kind": "service",
                    "ports": [8080],
                    "container": {"image": "web:v1"},
                },
            }
        )
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
                merged = patch_polyaxonfile(
                    source,
                    [
                        {"patchStrategy": strategy, "run": {"kind": "job"}},
                        {"run": {"container": {"image": "last:v2"}}},
                    ],
                )

                assert merged.run.container.image == "last:v2"
                if strategy in (PatchStrategy.POST_MERGE, PatchStrategy.REPLACE):
                    assert merged.run.kind == "job"
                    assert "ports" not in merged.run.to_dict()
                else:
                    assert merged.run.kind == "service"
                    assert merged.run.ports == [8080]

    def test_partial_file_run_patches_outer_runtime_before_component_composition(self):
        source = read_polyaxonfile(
            {
                "patchStrategy": "pre_merge",
                "component": {
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                },
                "run": {"kind": "service", "ports": [8080]},
            }
        )

        merged = patch_polyaxonfile(source, [{"run": {"ports": [9090]}}])

        assert merged.run.kind == "service"
        assert merged.run.ports == [8080, 9090]
        effective = compose_polyaxonfile(merged)
        assert effective.run.kind == "job"
        assert effective.run.container.image == "base:v1"

    def test_null_and_empty_run_patch_keep_fixed_legacy_results(self):
        retained_patch = {"container": {"image": "patch:v1"}}
        for definition, expected_empty in (
            (
                {"hubRef": "train:v1"},
                {
                    PatchStrategy.POST_MERGE: retained_patch,
                    PatchStrategy.PRE_MERGE: retained_patch,
                    PatchStrategy.REPLACE: {},
                    PatchStrategy.ISNULL: retained_patch,
                },
            ),
            (
                {
                    "component": {
                        "run": {"kind": "job", "container": {"image": "base:v1"}},
                    },
                },
                {
                    PatchStrategy.POST_MERGE: retained_patch,
                    PatchStrategy.PRE_MERGE: retained_patch,
                    PatchStrategy.REPLACE: retained_patch,
                    PatchStrategy.ISNULL: retained_patch,
                },
            ),
        ):
            source = {
                "kind": "operation",
                **definition,
                "runPatch": {"container": {"image": "patch:v1"}},
            }
            for strategy, want_empty in expected_empty.items():
                for value, want in ((None, retained_patch), ({}, want_empty)):
                    with self.subTest(
                        definition=definition, value=value, strategy=strategy
                    ):
                        overlay = {"patchStrategy": strategy, "runPatch": value}
                        merged = patch_polyaxonfile(
                            read_polyaxonfile(source), [overlay]
                        )
                        assert merged.run_patch == want
                        assert merged.to_dict()["runPatch"] == want
                        if "component" in definition:
                            compiled = OperationSpecification.compile_operation(merged)
                            assert compiled.run.to_dict() == {
                                "kind": "job",
                                "container": {"image": "patch:v1"},
                            }

    def test_model_overlays_preserve_nulls_without_changing_the_inputs(self):
        source = read_polyaxonfile(
            {
                "queue": "base",
                "isApproved": True,
                "params": {"count": 1},
                "run": {"kind": "job", "container": {"image": "base:v1"}},
            }
        )
        overlay = read_polyaxonfile(
            {
                "queue": None,
                "isApproved": False,
                "params": {},
                "patchStrategy": "replace",
            }
        )
        before_source, before_overlay = deepcopy(source), deepcopy(overlay)

        merged = patch_polyaxonfile(source, [overlay])

        assert merged.queue is None
        assert "queue" in merged.model_fields_set
        assert merged.is_approved is False
        assert merged.params == {}
        assert merged.run.container.image == "base:v1"
        assert "is_preset" not in merged.model_fields_set
        assert source == before_source
        assert overlay == before_overlay

    def test_run_patch_overlays_merge_like_native_on_shortcut_runtimes(self):
        container = {"image": "busybox:1.36"}
        operations = [{"name": "train", "container": container}]
        runtimes = (
            ({"container": container}, {"kind": "job", "container": container}),
            (
                {"container": container, "service": {"ports": [8080]}},
                {"kind": "service", "container": container, "ports": [8080]},
            ),
            (
                {"dag": {"operations": operations}},
                {"kind": "dag", "operations": operations},
            ),
        )
        first = {"connections": ["base"], "environment": {"labels": {"from": "base"}}}
        second = {
            "connections": ["overlay"],
            "environment": {"labels": {"from": "overlay"}, "annotations": {"new": "a"}},
        }
        for (shortcuts, native), strategy, wrapped in product(
            runtimes, PatchStrategy, (False, True)
        ):

            def merge(layer):
                source = {"component": layer} if wrapped else layer
                return patch_polyaxonfile(
                    read_polyaxonfile({**source, "runPatch": first}),
                    [{"patchStrategy": strategy, "runPatch": second}],
                )

            with self.subTest(kind=native["kind"], strategy=strategy, wrapped=wrapped):
                merged = merge(shortcuts)
                expected = merge({"run": native})
                assert merged.run_patch == expected.run_patch
                assert OperationSpecification.compile_operation(merged).run == (
                    OperationSpecification.compile_operation(expected).run
                )

    def test_run_patch_strategies_keep_new_fields_on_a_shortcut_runtime(self):
        for strategy, concurrency in (
            (PatchStrategy.POST_MERGE, 4),
            (PatchStrategy.PRE_MERGE, 2),
            (PatchStrategy.REPLACE, 4),
            (PatchStrategy.ISNULL, 2),
        ):
            with self.subTest(strategy=strategy):
                merged = patch_polyaxonfile(
                    read_polyaxonfile({"dag": {}, "runPatch": {"concurrency": 2}}),
                    [
                        {
                            "patchStrategy": strategy,
                            "runPatch": {"concurrency": 4, "connections": ["a"]},
                        }
                    ],
                )
                run = OperationSpecification.compile_operation(merged).run
                assert run.concurrency == concurrency
                assert run.connections == ["a"]

    def test_git_init_reaches_shortcut_runtimes_with_a_run_patch(self):
        git_init = V1Init(git=V1GitType(url="https://example.com/repo"))
        run_patch = {"connections": ["artifacts"]}
        container = {"image": "busybox:1.36"}
        for source in (
            {"container": container},
            {"container": container, "service": {}},
        ):
            with self.subTest(source=source):
                config = get_op_specification(
                    config=read_polyaxonfile({**source, "runPatch": run_patch}),
                    git_init=git_init,
                    validate_params=False,
                )
                run = OperationSpecification.compile_operation(config).run
                assert run.connections == ["artifacts"]
                assert run.init[0].git.url == "https://example.com/repo"
        # A DAG has no init: the patch fails instead of disappearing.
        with self.assertRaises(ValidationError):
            get_op_specification(
                config=read_polyaxonfile({"dag": {}, "runPatch": run_patch}),
                git_init=git_init,
                validate_params=False,
            )

    def test_kindless_run_overlay_merges_below_same_layer_shortcuts(self):
        def compile_with(source, overlay):
            merged = patch_polyaxonfile(read_polyaxonfile(source), [overlay])
            stored = read_polyaxonfile(merged.to_source_json())
            return OperationSpecification.compile_operation(stored).run

        section = {"dag": {"concurrency": 2}}
        for overlay, concurrency in (
            ({"run": {"concurrency": 4}}, 2),
            ({"run": {"kind": "dag", "concurrency": 4}}, 2),
            ({"runPatch": {"concurrency": 4}}, 4),
        ):
            with self.subTest(overlay=overlay):
                assert compile_with(section, overlay).concurrency == concurrency
        # Fields the section leaves alone still apply, and an outer layer wins.
        run = compile_with(section, {"run": {"connections": ["a"]}})
        assert run.connections == ["a"]
        run = compile_with({"component": section}, {"run": {"concurrency": 4}})
        assert run.concurrency == 4
        # One overlay can bring the section; a document cannot.
        overlay = {"dag": {}, "run": {"concurrency": 4}}
        assert compile_with({"queue": "default"}, overlay).concurrency == 4
        with self.assertRaisesRegex(ValidationError, "run.kind must be provided"):
            read_polyaxonfile(overlay)

    def test_native_runs_decide_overlays_before_shortcuts(self):
        job = {"kind": "job", "container": {"image": "busybox:1.36"}}
        patch = {"container": {"image": "busybox:1.37"}}
        dag_under_job = {"component": {"dag": {}}, "run": {"kind": "job"}}
        for source, overlays, kind in (
            # An overlay's section must not meet the runtime its `run` replaces.
            (
                {"component": {"run": job}, "run": patch},
                [{"run": {"kind": "service", **patch}, "service": {"ports": [8080]}}],
                "service",
            ),
            (
                {"component": {"run": job}, "run": patch},
                [{"run": None, "service": {"ports": [8080]}}],
                "service",
            ),
            # Shortcuts cleared by an overlay never meet the native run.
            (
                {"run": {"kind": "dag"}, "env": {"A": "1"}},
                [{"env": None, "run": {"concurrency": 4}}],
                "dag",
            ),
            (
                {
                    "run": {"kind": "dag"},
                    "env": {"A": "1"},
                    "runPatch": {"concurrency": 2},
                },
                [{"runPatch": {"concurrency": 4}}, {"env": None}],
                "dag",
            ),
            # These strategies keep the inherited DAG over the explicit job.
            (
                {"component": {**dag_under_job, "patchStrategy": "pre_merge"}},
                [{"run": {"concurrency": 4}}],
                "dag",
            ),
            (
                {"component": {**dag_under_job, "patchStrategy": "isnull"}},
                [{"run": {"concurrency": 4}}],
                "dag",
            ),
            # A cleared run leaves the layer's own section to choose.
            (
                {"component": {"run": job}, "run": None, "service": {}},
                [{"run": patch}],
                "service",
            ),
        ):
            with self.subTest(source=source):
                merged = patch_polyaxonfile(read_polyaxonfile(source), overlays)
                stored = read_polyaxonfile(merged.to_source_json())
                compiled = OperationSpecification.compile_operation(stored)
                assert compiled.run.kind == kind

    def test_run_lookup_leaves_authored_shortcuts_alone(self):
        config = read_polyaxonfile(
            {
                "container": {"image": "busybox:1.36"},
                "cmd": "echo train",
                "env": {"A": "1"},
            }
        )
        before = config.to_dict()

        assert config.get_native_run().kind == "job"

        assert config.to_dict() == before

    def test_explicit_null_runtime_uses_file_strategy_and_can_be_replaced(self):
        source = read_polyaxonfile(
            {"run": {"kind": "job", "container": {"image": "base:v1"}}}
        )
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
                merged = patch_polyaxonfile(
                    source, [{"run": None, "patchStrategy": strategy}]
                )
                if strategy in (PatchStrategy.POST_MERGE, PatchStrategy.REPLACE):
                    assert merged.run is None
                    assert "run" in merged.model_fields_set
                else:
                    assert merged.run.container.image == "base:v1"

        source = read_polyaxonfile({"component": source, "run": None})
        merged = patch_polyaxonfile(
            source, [{"run": {"container": {"image": "local:v2"}}}]
        )
        assert merged.run.kind == "job"
        assert compose_polyaxonfile(merged).run.container.image == "local:v2"
        assert source.run is None

    def test_file_fields_still_use_typed_validation(self):
        source = read_polyaxonfile({"run": {"kind": "job"}})
        for overlay in (
            {"unknown": True},
            {"patchStrategy": "unknown"},
            {"run": {"kind": None}},
            {"run": {"ports": [8080]}},
        ):
            with self.subTest(overlay=overlay), self.assertRaises(ValidationError):
                patch_polyaxonfile(source, [overlay])

        with self.assertRaises(ValidationError):
            patch_polyaxonfile(
                read_polyaxonfile({"run": {"kind": "dag"}}),
                [{"run": {"operations": ["not-a-node"]}}],
            )

        with self.assertRaisesRegex(
            PolyaxonValidationError, "run.kind must be provided"
        ):
            patch_polyaxonfile(
                read_polyaxonfile({"hubRef": "unresolved:v1"}),
                [{"run": {"container": {"image": "local:v2"}}}],
            )

    def test_file_overlay_reading_keeps_existing_input_forms(self):
        values = {
            "params": {"count": 5},
            "run": {"kind": "service", "container": {"image": "override:v2"}},
        }
        source = read_polyaxonfile(
            {"run": {"kind": "service", "container": {"image": "base:v1"}}}
        )
        before = source.to_dict()
        for overlay in (
            values,
            read_polyaxonfile(values),
            read_polyaxonfile(values).to_json(),
            [{"params": {"count": 3}}, values],
        ):
            with self.subTest(overlay=overlay):
                merged = patch_polyaxonfile(source, [overlay])

                assert merged.run.kind == "service"
                assert merged.run.container.image == "override:v2"
                assert merged.params["count"].value == 5
                assert source.to_dict() == before

    def test_file_override_cannot_relax_strict_component(self):
        source = read_polyaxonfile(
            {
                "component": {
                    "strictParams": True,
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                },
                "strictParams": True,
                "params": {"message": {"value": "hello", "contextOnly": True}},
            }
        )

        merged = patch_polyaxonfile(source, [{"strictParams": False}])
        effective = compose_polyaxonfile(merged)

        assert merged.strict_params is False
        assert effective.strict_params is True
        assert effective.params["message"].context_only is True

    def test_distributed_file_patches_keep_replica_fields(self):
        source = read_polyaxonfile(
            {
                "run": {
                    "kind": "pytorchjob",
                    "worker": {"replicas": 2, "container": {"image": "base:v1"}},
                },
                "runPatch": {"container": {"image": "initial:v2"}},
            }
        )
        merged = patch_polyaxonfile(
            source,
            [
                {
                    "runPatch": {
                        "container": {"image": "final:v3", "command": ["train"]},
                    },
                }
            ],
        )
        effective = compose_polyaxonfile(merged)

        assert merged.run.worker.container.image == "base:v1"
        assert effective.run.worker.replicas == 2
        assert effective.run.worker.container.image == "final:v3"
        assert effective.run.worker.container.command == ["train"]

    def test_mpi_run_patches_reach_launcher_and_worker(self):
        launcher = {"replicas": 1, "container": {"image": "base:v1"}}
        compiled = OperationSpecification.compile_operation(
            read_polyaxonfile(
                {
                    "run": {
                        "kind": "mpijob",
                        "slotsPerWorker": 2,
                        "launcher": deepcopy(launcher),
                        "worker": {"replicas": 2, "container": {"image": "base:v1"}},
                    },
                    "runPatch": {"container": {"image": "patched:v2"}},
                }
            )
        )
        assert compiled.run.slots_per_worker == 2
        assert compiled.run.launcher.replicas == 1
        assert compiled.run.worker.replicas == 2
        assert compiled.run.launcher.container.image == "patched:v2"
        assert compiled.run.worker.container.image == "patched:v2"

        def compile_launcher_only(run_patch):
            return OperationSpecification.compile_operation(
                read_polyaxonfile(
                    {
                        "run": {"kind": "mpijob", "launcher": deepcopy(launcher)},
                        "runPatch": run_patch,
                    }
                )
            ).run

        # Generic patches reach existing roles only; MPI-level and role-shaped
        # patches keep their native behavior, including creating a named role.
        run = compile_launcher_only({"container": {"image": "patched:v2"}})
        assert run.launcher.container.image == "patched:v2"
        assert run.worker is None
        run = compile_launcher_only({"slotsPerWorker": 4})
        assert run.slots_per_worker == 4
        assert run.launcher.container.image == "base:v1"
        run = compile_launcher_only(
            {"worker": {"replicas": 3, "container": {"image": "worker:v2"}}}
        )
        assert run.launcher.container.image == "base:v1"
        assert run.worker.replicas == 3
        assert run.worker.container.image == "worker:v2"
