from copy import deepcopy
import pytest

from clipped.compact.pydantic import ValidationError
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
    get_specification,
    read_polyaxonfile,
)
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.polyaxonfile_mark
class TestShortcuts(BaseTestCase):
    def test_container_compiles_like_native_run_container(self):
        container = {
            "image": "busybox:1.36",
            "command": ["echo"],
            "args": ["hello"],
        }
        native = OperationSpecification.compile_operation(
            read_polyaxonfile({"run": {"kind": "job", "container": container}})
        )
        sources = [
            {"container": container},
            {"kind": "component", "container": container},
            {"kind": "operation", "container": container},
            {"kind": "operation", "component": {"container": container}},
        ]
        for source in sources:
            with self.subTest(source=source):
                authored = get_specification(deepcopy(source))
                before = authored.to_dict()

                compiled = OperationSpecification.compile_operation(authored)

                assert compiled.run == native.run
                assert authored.to_dict() == before
                saved = read_polyaxonfile(authored.to_source_json())
                assert saved.to_dict() == before
                assert "run" not in saved.model_fields_set

    def test_container_applies_between_run_and_run_patch(self):
        def image(source):
            compiled = OperationSpecification.compile_operation(
                read_polyaxonfile(deepcopy(source))
            )
            return compiled.run.container.image

        layer = {
            "run": {"kind": "job", "container": {"image": "native:v1"}},
            "container": {"image": "root:v1"},
        }
        with_patch = {**layer, "runPatch": {"container": {"image": "patch:v1"}}}

        assert image(layer) == "root:v1"
        assert image(with_patch) == "patch:v1"
        assert image({"kind": "operation", "component": with_patch}) == "patch:v1"
        # Outer layers override inner ones regardless of spelling.
        outer_native = {"run": {"kind": "job", "container": {"image": "outer:v1"}}}
        assert image({**outer_native, "component": layer}) == "outer:v1"
        assert image({**outer_native, "component": with_patch}) == "outer:v1"
        assert (
            image({"container": {"image": "outer:v2"}, "component": layer})
            == "outer:v2"
        )

    def test_container_keeps_the_inherited_runtime_kind(self):
        service = {
            "run": {
                "kind": "service",
                "ports": [8080],
                "container": {"image": "base:v1", "command": ["serve"]},
            }
        }
        compiled = OperationSpecification.compile_operation(
            read_polyaxonfile(
                {"container": {"image": "overlay:v1"}, "component": service}
            )
        )
        assert compiled.run.kind == "service"
        assert compiled.run.ports == [8080]
        assert compiled.run.container.image == "overlay:v1"
        assert compiled.run.container.command == ["serve"]

        dag = {
            "run": {
                "kind": "dag",
                "operations": [{"name": "first", "dagRef": "task"}],
                "components": [
                    {
                        "name": "task",
                        "run": {"kind": "job", "container": {"image": "base:v1"}},
                    }
                ],
            }
        }
        OperationSpecification.compile_operation(read_polyaxonfile(deepcopy(dag)))
        authored = read_polyaxonfile({**dag, "container": {"image": "busybox:1.36"}})
        with self.assertRaises(ValidationError):
            OperationSpecification.compile_operation(authored)

    def test_named_preset_applies_container_before_its_run_patch(self):
        def compile_service():
            return OperationSpecification.compile_operation(
                read_polyaxonfile(
                    {
                        "run": {
                            "kind": "service",
                            "ports": [8080],
                            "container": {"image": "base:v1", "command": ["serve"]},
                        }
                    }
                )
            )

        compiled = CompiledOperationSpecification.apply_preset(
            compile_service(), {"container": {"image": "preset:v1"}}
        )
        assert compiled.run.kind == "service"
        assert compiled.run.ports == [8080]
        assert compiled.run.container.image == "preset:v1"
        assert compiled.run.container.command == ["serve"]

        compiled = CompiledOperationSpecification.apply_preset(
            compile_service(),
            {
                "container": {"image": "preset:v1"},
                "runPatch": {"container": {"image": "patch:v1"}},
            },
        )
        assert compiled.run.container.image == "patch:v1"
