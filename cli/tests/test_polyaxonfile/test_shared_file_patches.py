from copy import deepcopy
from pathlib import Path
import pytest
from tempfile import TemporaryDirectory
import yaml

from clipped.compact.pydantic import ValidationError
from clipped.config.patch_strategy import PatchStrategy
from polyaxon._polyaxonfile import (
    OperationSpecification,
    compose_polyaxonfile,
    get_op_specification,
    patch_polyaxonfile,
    read_polyaxonfile,
)
from polyaxon._polyaxonfile.check import collect_references
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.polyaxonfile_mark
class TestSharedFilePatches(BaseTestCase):
    def test_multiple_files_match_legacy_cli_patch_order(self):
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
            legacy = get_op_specification(
                config=OperationSpecification.read(str(base)),
                preset_files=overlays,
                validate_params=False,
            )

        assert merged.to_dict() == legacy.to_dict()
        assert source == before
        assert merged.component.run.container.image == "base:v1"
        assert merged.run_patch["container"]["image"] == "first:v2"
        assert merged.run_patch["environment"]["annotations"] == {"source": "second"}
        assert merged.patch_strategy is None
        effective = compose_polyaxonfile(merged)
        compiled = OperationSpecification.compile_operation(legacy)
        assert effective.run.to_dict() == compiled.run.to_dict()
        assert effective.run.container.image == "first:v2"

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
                    assert {k: p.value for k, p in merged.params.items()} == want["params"]
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
                "params: {count: 5}\n"
                "run: {container: {image: second:v3}}\n"
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

    def test_run_patch_waits_for_runtime_kind_from_later_file(self):
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
            second.write_text(
                "run: {kind: service, container: {image: server:v2}}\n"
            )

            merged = patch_polyaxonfile(source, [str(first), str(second)])

        assert merged.run.kind == "service"
        assert merged.run.ports is None
        assert merged.run_patch["ports"] == [8080]
        effective = compose_polyaxonfile(merged)
        assert effective.run.ports == [8080]
        assert effective.run.environment.annotations == {"source": "first"}
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

    def test_null_and_empty_run_patch_match_legacy_with_or_without_runtime(self):
        for definition in (
            {"hubRef": "train:v1"},
            {
                "component": {
                    "run": {"kind": "job", "container": {"image": "base:v1"}},
                },
            },
        ):
            source = {
                "kind": "operation",
                **definition,
                "runPatch": {"container": {"image": "patch:v1"}},
            }
            for value in (None, {}):
                for strategy in PatchStrategy:
                    with self.subTest(
                        definition=definition, value=value, strategy=strategy
                    ):
                        overlay = {"patchStrategy": strategy, "runPatch": value}
                        merged = patch_polyaxonfile(read_polyaxonfile(source), [overlay])
                        legacy = OperationSpecification.read(deepcopy(source))
                        preset = OperationSpecification.read(
                            deepcopy(overlay), is_preset=True
                        )
                        legacy.patch(preset, strategy=strategy)

                        assert merged.to_dict() == legacy.to_dict()

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
                read_polyaxonfile({"hubRef": "unresolved:v1"}),
                [{"run": {"container": {"image": "local:v2"}}}],
            )

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
