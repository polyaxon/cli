from copy import deepcopy
import pytest

from clipped.compact.pydantic import ValidationError
from clipped.config.patch_strategy import PatchStrategy
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
    get_specification,
    patch_polyaxonfile,
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

    def test_cmd_compiles_to_one_shell_script(self):
        def compile_container(cmd):
            authored = read_polyaxonfile(
                {"container": {"image": "busybox:1.36"}, "cmd": deepcopy(cmd)}
            )
            before = authored.to_dict()
            compiled = OperationSpecification.compile_operation(authored)
            assert authored.to_dict() == before
            assert read_polyaxonfile(authored.to_source_json()).cmd == cmd
            assert compiled.run.kind == "job"
            assert compiled.run.container.image == "busybox:1.36"
            assert compiled.run.container.command == ["/bin/sh", "-c"]
            return compiled.run.container.args

        assert compile_container("python train.py") == ["set -e\npython train.py"]
        assert compile_container(["python train.py"]) == ["set -e\npython train.py"]
        lines = [
            "export MESSAGE=hello",
            'cd work && printf "%s\\n" "$MESSAGE"',
            "echo {{ globals.uuid }}",
        ]
        script = "set -e\n" + "\n".join(lines)
        assert compile_container(lines) == [script]
        assert compile_container("\n".join(lines)) == [script]

    def test_cmd_rejects_blank_and_wrong_types(self):
        for cmd in ("", "  ", [], ["ok", " "], [1], {"a": "b"}, True):
            with self.subTest(cmd=cmd), self.assertRaises(ValidationError):
                V1Polyaxonfile.from_dict({"cmd": cmd})
        with self.assertRaisesRegex(ValidationError, r"cmd\[1\]"):
            V1Polyaxonfile.from_dict({"cmd": ["ok", " "]})

    def test_cmd_replaces_or_keeps_the_whole_command_pair(self):
        shell = (["/bin/sh", "-c"], ["set -e\necho hi"])
        for argv in (
            {"command": ["python"], "args": ["train.py"]},
            {"command": ["python", "train.py"]},
            {"args": ["--lr", "0.1"]},
            {},
        ):
            base = {
                "run": {
                    "kind": "job",
                    "container": {"image": "base:v1", **argv},
                }
            }
            existing = (argv.get("command"), argv.get("args")) if argv else shell
            for strategy, expected in (
                (PatchStrategy.POST_MERGE, shell),
                (PatchStrategy.REPLACE, shell),
                (PatchStrategy.PRE_MERGE, existing),
                (PatchStrategy.ISNULL, existing),
            ):
                with self.subTest(argv=argv, strategy=strategy):
                    compiled = OperationSpecification.compile_operation(
                        read_polyaxonfile(
                            {
                                "patchStrategy": strategy,
                                "cmd": "echo hi",
                                "component": deepcopy(base),
                            }
                        )
                    )
                    container = compiled.run.container
                    assert container.image == "base:v1"
                    assert (container.command, container.args) == expected

    def test_cmd_keeps_each_replica_argv_under_pre_merge(self):
        replica = {"replicas": 1, "container": {"image": "base:v1"}}
        compiled = OperationSpecification.compile_operation(
            read_polyaxonfile(
                {
                    "patchStrategy": PatchStrategy.PRE_MERGE,
                    "cmd": "echo hi",
                    "component": {
                        "run": {
                            "kind": "pytorchjob",
                            "master": {
                                "replicas": 1,
                                "container": {
                                    "image": "base:v1",
                                    "command": ["torchrun"],
                                },
                            },
                            "worker": replica,
                        }
                    },
                }
            )
        )
        assert compiled.run.master.container.command == ["torchrun"]
        assert compiled.run.master.container.args is None
        assert compiled.run.worker.container.command == ["/bin/sh", "-c"]
        assert compiled.run.worker.container.args == ["set -e\necho hi"]
        assert compiled.run.worker.replicas == 1

    def test_cmd_overlays_replace_or_keep_the_whole_script(self):
        base = {"container": {"image": "busybox:1.36"}, "cmd": ["echo a", "echo b"]}
        for strategy, expected in (
            (None, "echo c"),
            (PatchStrategy.REPLACE, "echo c"),
            (PatchStrategy.PRE_MERGE, ["echo a", "echo b"]),
            (PatchStrategy.ISNULL, ["echo a", "echo b"]),
        ):
            with self.subTest(strategy=strategy):
                overlay = {"cmd": "echo c"}
                if strategy:
                    overlay["patchStrategy"] = strategy
                config = patch_polyaxonfile(deepcopy(base), [overlay])
                assert config.cmd == expected

        compiled = OperationSpecification.compile_operation(
            read_polyaxonfile(deepcopy(base)), override={"cmd": ["echo c"]}
        )
        assert compiled.run.container.args == ["set -e\necho c"]

    def test_cmd_applies_after_container_and_before_run_patch(self):
        compiled = OperationSpecification.compile_operation(
            read_polyaxonfile(
                {
                    "run": {
                        "kind": "job",
                        "container": {
                            "image": "native:v1",
                            "command": ["python"],
                            "args": ["train.py"],
                        },
                    },
                    "container": {"command": ["echo"], "args": ["container"]},
                    "cmd": "echo cmd",
                    "runPatch": {"container": {"image": "patch:v1"}},
                }
            )
        )
        assert compiled.run.container.image == "patch:v1"
        assert compiled.run.container.command == ["/bin/sh", "-c"]
        assert compiled.run.container.args == ["set -e\necho cmd"]

    def test_named_preset_applies_cmd(self):
        compiled = OperationSpecification.compile_operation(
            read_polyaxonfile(
                {
                    "run": {
                        "kind": "service",
                        "ports": [8080],
                        "container": {
                            "image": "base:v1",
                            "command": ["serve"],
                            "args": ["--port", "8080"],
                        },
                    }
                }
            )
        )
        kept = CompiledOperationSpecification.apply_preset(
            compiled.clone(), {"cmd": ["serve --fast"], "patchStrategy": "pre_merge"}
        )
        assert kept.run.container.command == ["serve"]
        assert kept.run.container.args == ["--port", "8080"]

        compiled = CompiledOperationSpecification.apply_preset(
            compiled, {"cmd": ["serve --fast"]}
        )
        assert compiled.run.kind == "service"
        assert compiled.run.container.image == "base:v1"
        assert compiled.run.container.command == ["/bin/sh", "-c"]
        assert compiled.run.container.args == ["set -e\nserve --fast"]
