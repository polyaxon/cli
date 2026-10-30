from copy import deepcopy
from itertools import product
from mock import patch
import os
import pytest
import re
import subprocess
import tempfile

from clipped.compact.pydantic import ValidationError
from clipped.config.patch_strategy import PatchStrategy
from clipped.utils.json import orjson_dumps, orjson_loads
from clipped.utils.units import to_cpu_value, to_memory_bytes
from polyaxon._flow.polyaxonfile import V1Polyaxonfile, _dedupe_env
from polyaxon._k8s import k8s_schemas
from polyaxon._k8s.converter.common.accelerators import requests_gpu
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
    check_polyaxonfile,
    get_shortcuts,
    get_specification,
    patch_polyaxonfile,
    read_polyaxonfile,
)
from polyaxon._polyaxonfile.shortcuts import (
    SHORTCUT_KEYS,
    get_shortcut_specification,
    validate_shortcuts,
)
from polyaxon._polyaxonfile.specs import compose_polyaxonfile
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon._vendor.k8s.quantity import parse_quantity
from polyaxon.exceptions import PolyaxonfileError, PolyaxonValidationError
from polyaxon.schemas import V1DagShortcut, V1Operation


SECRET = {"secretKeyRef": {"name": "secrets", "key": "token"}}
# Runtime-field shortcut values: an inherited one and an incoming one.
BASE_RUNTIME = {
    "environment": {"nodeSelector": {"pool": "base"}, "labels": {"team": "a"}},
    "init": [{"container": {"name": "base", "image": "busybox:1.36"}}],
    "connections": ["base"],
    "sidecars": [{"name": "base", "image": "busybox:1.36"}],
    "volumes": [{"name": "base", "emptyDir": {}}],
}
NEW_RUNTIME = {
    "environment": {"nodeSelector": {"pool": "new"}},
    "init": [{"container": {"name": "new", "image": "busybox:1.36"}}],
    "connections": ["new"],
    "sidecars": [{"name": "new", "image": "busybox:1.36"}],
    "volumes": [{"name": "new", "emptyDir": {}}],
}


def _env(container):
    """(name, value, has valueFrom) per entry, for typed and dict entries."""
    result = []
    for entry in container.env or []:
        if isinstance(entry, dict):
            value_from = entry.get("valueFrom") or entry.get("value_from")
            result.append((entry["name"], entry.get("value"), value_from is not None))
        else:
            result.append((entry.name, entry.value, entry.value_from is not None))
    return result


def _compile(source):
    return OperationSpecification.compile_operation(read_polyaxonfile(deepcopy(source)))


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

    def test_cmd_reaches_containers_created_later(self):
        pair = (["/bin/sh", "-c"], ["set -e\necho hi"])
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy, image="same-layer runPatch"):
                compiled = OperationSpecification.compile_operation(
                    read_polyaxonfile(
                        {
                            "run": {"kind": "job"},
                            "patchStrategy": strategy,
                            "cmd": "echo hi",
                            "runPatch": {"container": {"image": "busybox:1.36"}},
                        }
                    )
                )
                container = compiled.run.container
                assert container.image == "busybox:1.36"
                assert (container.command, container.args) == pair

            with self.subTest(strategy=strategy, image="named preset"):
                compiled = OperationSpecification.compile_operation(
                    read_polyaxonfile(
                        {
                            "run": {"kind": "job"},
                            "patchStrategy": strategy,
                            "cmd": "echo hi",
                        }
                    )
                )
                compiled = CompiledOperationSpecification.apply_preset(
                    compiled, {"container": {"image": "busybox:1.36"}}
                )
                container = compiled.run.container
                assert container.image == "busybox:1.36"
                assert (container.command, container.args) == pair

    def test_cmd_rejects_unsupported_runtimes(self):
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
        compiled = OperationSpecification.compile_operation(
            read_polyaxonfile(deepcopy(dag))
        )
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy, path="composition"):
                authored = read_polyaxonfile(
                    {**deepcopy(dag), "patchStrategy": strategy, "cmd": "echo hi"}
                )
                with self.assertRaises(ValidationError):
                    OperationSpecification.compile_operation(authored)
            with self.subTest(strategy=strategy, path="named preset"):
                with self.assertRaises(ValidationError):
                    CompiledOperationSpecification.apply_preset(
                        compiled.clone(),
                        {"patchStrategy": strategy, "cmd": "echo hi"},
                    )

    def test_cmd_keeps_unresolved_replica_references(self):
        for strategy in (PatchStrategy.PRE_MERGE, PatchStrategy.ISNULL):
            with self.subTest(strategy=strategy):
                compiled = OperationSpecification.compile_operation(
                    read_polyaxonfile(
                        {
                            "patchStrategy": strategy,
                            "cmd": "echo hi",
                            "component": {
                                "run": {
                                    "kind": "pytorchjob",
                                    "master": {
                                        "replicas": 1,
                                        "container": {"image": "base:v1"},
                                    },
                                    "worker": "{{ params.replica }}",
                                }
                            },
                        }
                    )
                )
                assert compiled.run.worker == "{{ params.replica }}"
                assert compiled.run.master.container.command == ["/bin/sh", "-c"]
                assert compiled.run.master.container.args == ["set -e\necho hi"]

    def test_cmd_alone_null_and_source_replay(self):
        compiled = OperationSpecification.compile_operation(
            read_polyaxonfile({"cmd": "echo hi"})
        )
        assert compiled.run.kind == "job"
        assert compiled.run.container.command == ["/bin/sh", "-c"]
        assert compiled.run.container.args == ["set -e\necho hi"]

        source = {
            "run": {
                "kind": "job",
                "container": {"image": "base:v1", "command": ["python"]},
            },
            "cmd": None,
        }
        authored = read_polyaxonfile(deepcopy(source))
        compiled = OperationSpecification.compile_operation(authored)
        assert compiled.run.container.command == ["python"]
        assert compiled.run.container.args is None
        replayed = read_polyaxonfile(authored.to_source_json())
        assert "cmd" in replayed.model_fields_set
        assert replayed.cmd is None

    def test_cmd_script_runs_in_one_shell_and_stops_on_failure(self):
        def run(cmd):
            compiled = OperationSpecification.compile_operation(
                read_polyaxonfile({"cmd": cmd})
            )
            container = compiled.run.container
            return subprocess.run(
                container.command + container.args,
                capture_output=True,
                text=True,
                check=False,
            )

        result = run(["export MESSAGE=hello", "cd /", 'echo "$MESSAGE $PWD"'])
        assert result.returncode == 0, result.stderr
        assert result.stdout == "hello /\n"

        result = run(["echo before", "false", "echo after"])
        assert result.returncode != 0
        assert result.stdout == "before\n"

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

    def test_env_lowers_to_main_container_entries(self):
        env = {
            "LOG_LEVEL": "debug",
            "EMPTY": "",
            "DSN": "user=a;opts=b=c",
            "RUN": "{{ globals.uuid }}",
        }
        authored = read_polyaxonfile(
            {"container": {"image": "busybox:1.36"}, "env": deepcopy(env)}
        )
        before = authored.to_dict()
        compiled = OperationSpecification.compile_operation(authored)
        assert compiled.run.kind == "job"
        assert _env(compiled.run.container) == [
            (name, value, False) for name, value in env.items()
        ]
        assert authored.to_dict() == before
        assert read_polyaxonfile(authored.to_source_json()).env == env

    def test_env_rejects_wrong_types_with_a_quoting_hint(self):
        for value, hint in ((3, '"3"'), (True, '"true"'), (0.5, '"0.5"')):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    ValidationError, r"env\.RETRIES must be a string; quote it: " + hint
                ):
                    V1Polyaxonfile.from_dict({"env": {"RETRIES": value}})
        for env in ("A=1", ["A=1"], {"A": None}, {"A": ["x"]}):
            with self.subTest(env=env), self.assertRaises(ValidationError):
                V1Polyaxonfile.from_dict({"env": env})

    def test_env_merges_by_name_per_strategy(self):
        base = {
            "run": {
                "kind": "job",
                "container": {
                    "image": "base:v1",
                    "env": [
                        {"name": "SHARED", "value": "old"},
                        {"name": "TOKEN", "valueFrom": SECRET},
                        {"name": "KEEP", "value": "1"},
                    ],
                },
            }
        }
        env = {"SHARED": "new", "TOKEN": "literal", "ADDED": "x"}
        for strategy, expected in (
            (
                PatchStrategy.POST_MERGE,
                [
                    ("KEEP", "1", False),
                    ("SHARED", "new", False),
                    ("TOKEN", "literal", False),
                    ("ADDED", "x", False),
                ],
            ),
            (
                PatchStrategy.PRE_MERGE,
                [
                    ("ADDED", "x", False),
                    ("SHARED", "old", False),
                    ("TOKEN", None, True),
                    ("KEEP", "1", False),
                ],
            ),
            (
                PatchStrategy.REPLACE,
                [
                    ("SHARED", "new", False),
                    ("TOKEN", "literal", False),
                    ("ADDED", "x", False),
                ],
            ),
            (
                PatchStrategy.ISNULL,
                [
                    ("SHARED", "old", False),
                    ("TOKEN", None, True),
                    ("KEEP", "1", False),
                ],
            ),
        ):
            with self.subTest(strategy=strategy):
                compiled = _compile(
                    {"patchStrategy": strategy, "env": env, "component": base}
                )
                assert _env(compiled.run.container) == expected

    def test_env_wins_even_when_native_merging_drops_an_equal_entry(self):
        base = {
            "run": {
                "kind": "job",
                "container": {
                    "image": "base:v1",
                    "env": [
                        {"name": "A", "value": "x"},
                        {"name": "A", "value": "y"},
                    ],
                },
            }
        }
        for strategy, expected in (
            (PatchStrategy.POST_MERGE, [("A", "x", False)]),
            (PatchStrategy.PRE_MERGE, [("A", "y", False)]),
            (PatchStrategy.ISNULL, [("A", "x", False), ("A", "y", False)]),
        ):
            with self.subTest(strategy=strategy):
                compiled = _compile(
                    {"patchStrategy": strategy, "env": {"A": "x"}, "component": base}
                )
                assert _env(compiled.run.container) == expected

    def test_env_keeps_winner_positions_when_entries_are_equal(self):
        # Kubernetes expands $(B) only when B is defined earlier in the list.
        source = {
            "patchStrategy": PatchStrategy.POST_MERGE,
            "env": {"B": "hello", "A": "$(B)"},
            "component": {
                "run": {
                    "kind": "job",
                    "container": {
                        "image": "base:v1",
                        "env": [{"name": "A", "value": "$(B)"}],
                    },
                }
            },
        }
        authored = read_polyaxonfile(deepcopy(source))
        for config in (authored, read_polyaxonfile(authored.to_source_json())):
            compiled = OperationSpecification.compile_operation(config)
            assert _env(compiled.run.container) == [
                ("B", "hello", False),
                ("A", "$(B)", False),
            ]
            assert all(
                isinstance(entry, k8s_schemas.V1EnvVar)
                for entry in compiled.run.container.env
            )

        compiled = _compile(
            {
                "patchStrategy": PatchStrategy.PRE_MERGE,
                "env": {"B": "y", "A": "z"},
                "component": {
                    "run": {
                        "kind": "job",
                        "container": {
                            "image": "base:v1",
                            "env": [
                                {"name": "A", "value": "x"},
                                {"name": "B", "value": "y"},
                            ],
                        },
                    }
                },
            }
        )
        assert _env(compiled.run.container) == [("A", "x", False), ("B", "y", False)]

    def test_env_with_same_layer_container_env(self):
        for strategy, expected in (
            (PatchStrategy.POST_MERGE, [("B", "c", False), ("A", "s", False)]),
            (PatchStrategy.PRE_MERGE, [("A", "c", False), ("B", "c", False)]),
            (PatchStrategy.REPLACE, [("A", "s", False)]),
            (PatchStrategy.ISNULL, [("A", "c", False), ("B", "c", False)]),
        ):
            with self.subTest(strategy=strategy):
                compiled = _compile(
                    {
                        "patchStrategy": strategy,
                        "run": {"kind": "job", "container": {"image": "base:v1"}},
                        "container": {
                            "env": [
                                {"name": "A", "value": "c"},
                                {"name": "B", "value": "c"},
                            ]
                        },
                        "env": {"A": "s"},
                    }
                )
                assert _env(compiled.run.container) == expected

    def test_env_dedupe_matches_the_converter(self):
        typed = k8s_schemas.V1EnvVar(name="A", value="1")
        unnamed = {"value": "x", "valueFrom": None}
        env = [
            typed,
            {"name": "B", "value": "1"},
            unnamed,
            {"A": "2"},
            {"name": "B", "valueFrom": SECRET},
        ]
        assert _dedupe_env(env) == [unnamed, {"A": "2"}, env[-1]]

    def test_env_keeps_deferred_container_env(self):
        base = {
            "run": {
                "kind": "job",
                "container": {"image": "base:v1", "env": "{{ env_vars }}"},
            }
        }
        for strategy in (PatchStrategy.PRE_MERGE, PatchStrategy.ISNULL):
            with self.subTest(strategy=strategy):
                compiled = _compile(
                    {"patchStrategy": strategy, "env": {"A": "1"}, "component": base}
                )
                assert compiled.run.container.env == "{{ env_vars }}"

    def test_env_reaches_mpi_roles(self):
        a, b = ("A", "1", False), ("B", "x", False)
        expected = {
            "existing": {
                PatchStrategy.POST_MERGE: [a, b],
                PatchStrategy.PRE_MERGE: [b, a],
                PatchStrategy.REPLACE: [b],
                PatchStrategy.ISNULL: [a],
            },
            "empty": {
                PatchStrategy.POST_MERGE: [b],
                PatchStrategy.PRE_MERGE: [b],
                PatchStrategy.REPLACE: [b],
                PatchStrategy.ISNULL: [],
            },
            "omitted": {strategy: [b] for strategy in PatchStrategy},
        }
        env_by_case = {
            "existing": [{"name": "A", "value": "1"}],
            "empty": [],
            "omitted": None,
        }
        for case, strategy in product(env_by_case, PatchStrategy):
            with self.subTest(case=case, strategy=strategy):
                container = {"image": "base:v1"}
                if env_by_case[case] is not None:
                    container["env"] = env_by_case[case]
                replica = {"replicas": 1, "container": container}
                compiled = _compile(
                    {
                        "patchStrategy": strategy,
                        "env": {"B": "x"},
                        "component": {
                            "run": {
                                "kind": "mpijob",
                                "launcher": deepcopy(replica),
                                "worker": deepcopy(replica),
                            }
                        },
                    }
                )
                for role in (compiled.run.launcher, compiled.run.worker):
                    assert _env(role.container) == expected[case][strategy]

    def test_env_fills_a_role_created_by_the_patch(self):
        compiled = _compile(
            {
                "patchStrategy": PatchStrategy.PRE_MERGE,
                "env": {"A": "x"},
                "component": {
                    "run": {
                        "kind": "pytorchjob",
                        "master": {
                            "replicas": 1,
                            "container": {
                                "image": "base:v1",
                                "env": [{"name": "A", "value": "m"}],
                            },
                        },
                        "worker": {"replicas": 1},
                    }
                },
            }
        )
        assert _env(compiled.run.master.container) == [("A", "m", False)]
        assert _env(compiled.run.worker.container) == [("A", "x", False)]

    def test_env_normalizes_each_replica(self):
        def replica(*entries):
            return {
                "replicas": 1,
                "container": {
                    "image": "base:v1",
                    "env": [{"name": n, "value": v} for n, v in entries],
                },
            }

        compiled = _compile(
            {
                "env": {"B": "x"},
                "component": {
                    "run": {
                        "kind": "pytorchjob",
                        "master": replica(("A", "m1"), ("A", "m2")),
                        "worker": replica(("A", "w")),
                    }
                },
            }
        )
        assert _env(compiled.run.master.container) == [
            ("A", "m2", False),
            ("B", "x", False),
        ]
        assert _env(compiled.run.worker.container) == [
            ("A", "w", False),
            ("B", "x", False),
        ]

    def test_env_reaches_containers_created_later_and_rejects_dags(self):
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
                compiled = _compile(
                    {
                        "run": {"kind": "job"},
                        "patchStrategy": strategy,
                        "env": {"A": "1"},
                        "runPatch": {"container": {"image": "busybox:1.36"}},
                    }
                )
                assert compiled.run.container.image == "busybox:1.36"
                assert _env(compiled.run.container) == [("A", "1", False)]

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
        compiled = _compile(dag)
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy, path="composition"):
                authored = read_polyaxonfile(
                    {**deepcopy(dag), "patchStrategy": strategy, "env": {"A": "1"}}
                )
                with self.assertRaises(ValidationError):
                    OperationSpecification.compile_operation(authored)
            with self.subTest(strategy=strategy, path="named preset"):
                with self.assertRaises(ValidationError):
                    CompiledOperationSpecification.apply_preset(
                        compiled.clone(),
                        {"patchStrategy": strategy, "env": {"A": "1"}},
                    )

    def test_env_alone_empty_null_and_replay(self):
        compiled = _compile({"env": {"A": "1"}})
        assert compiled.run.kind == "job"
        assert _env(compiled.run.container) == [("A", "1", False)]

        base = {
            "run": {
                "kind": "job",
                "container": {
                    "image": "base:v1",
                    "env": [{"name": "A", "value": "1"}],
                },
            }
        }
        for strategy in (PatchStrategy.POST_MERGE, PatchStrategy.PRE_MERGE):
            with self.subTest(strategy=strategy, env={}):
                compiled = _compile(
                    {"patchStrategy": strategy, "env": {}, "component": base}
                )
                assert _env(compiled.run.container) == [("A", "1", False)]
        compiled = _compile(
            {"patchStrategy": PatchStrategy.REPLACE, "env": {}, "component": base}
        )
        assert not compiled.run.container.env

        authored = read_polyaxonfile({**deepcopy(base), "env": {"B": "2"}})
        for nulled in (
            patch_polyaxonfile(authored.clone(), [{"env": None}]),
            read_polyaxonfile(
                patch_polyaxonfile(authored.clone(), [{"env": None}]).to_source_json()
            ),
        ):
            assert "env" in nulled.model_fields_set
            assert nulled.env is None
            compiled = OperationSpecification.compile_operation(nulled)
            assert _env(compiled.run.container) == [("A", "1", False)]
        compiled = OperationSpecification.compile_operation(
            authored.clone(), override={"env": None}
        )
        assert _env(compiled.run.container) == [("A", "1", False)]

    def test_env_overlays_merge_by_key(self):
        base = {"container": {"image": "busybox:1.36"}, "env": {"A": "1", "B": "1"}}
        for strategy, expected in (
            (None, {"A": "1", "B": "2", "C": "2"}),
            (PatchStrategy.PRE_MERGE, {"A": "1", "B": "1", "C": "2"}),
            (PatchStrategy.REPLACE, {"B": "2", "C": "2"}),
            (PatchStrategy.ISNULL, {"A": "1", "B": "1"}),
        ):
            with self.subTest(strategy=strategy):
                overlay = {"env": {"B": "2", "C": "2"}}
                if strategy:
                    overlay["patchStrategy"] = strategy
                assert patch_polyaxonfile(deepcopy(base), [overlay]).env == expected

    def test_env_keeps_sidecars_and_applies_in_named_presets(self):
        compiled = _compile(
            {
                "run": {
                    "kind": "job",
                    "container": {"image": "base:v1"},
                    "sidecars": [
                        {
                            "name": "side",
                            "image": "side:v1",
                            "env": [{"name": "A", "value": "side"}],
                        }
                    ],
                },
                "env": {"A": "main"},
            }
        )
        assert _env(compiled.run.container) == [("A", "main", False)]
        assert _env(compiled.run.sidecars[0]) == [("A", "side", False)]

        service = _compile(
            {
                "run": {
                    "kind": "service",
                    "ports": [8080],
                    "container": {
                        "image": "base:v1",
                        "env": [{"name": "A", "value": "1"}],
                    },
                }
            }
        )
        kept = CompiledOperationSpecification.apply_preset(
            service.clone(), {"env": {"A": "2", "B": "2"}, "patchStrategy": "pre_merge"}
        )
        assert _env(kept.run.container) == [("B", "2", False), ("A", "1", False)]
        applied = CompiledOperationSpecification.apply_preset(
            service, {"env": {"A": "2"}}
        )
        assert applied.run.kind == "service"
        assert _env(applied.run.container) == [("A", "2", False)]

    def test_resources_lowers_each_value_form(self):
        for resources, requests, limits in (
            ({"cpu": 4}, {"cpu": 4}, None),
            ({"cpu": "4.."}, {"cpu": "4"}, None),
            ({"cpu": "..4"}, None, {"cpu": "4"}),
            ({"cpu": "500m..1"}, {"cpu": "500m"}, {"cpu": "1"}),
            ({"cpu": "4..4"}, {"cpu": "4"}, {"cpu": "4"}),
            ({"memory": "512Mi..1Gi"}, {"memory": "512Mi"}, {"memory": "1Gi"}),
            ({"memory": "16Gi"}, {"memory": "16Gi"}, None),
            ({"memory": "1.1Ki..1126.4"}, {"memory": "1.1Ki"}, {"memory": "1126.4"}),
            ({"gpu": 1}, {"nvidia.com/gpu": 1}, {"nvidia.com/gpu": 1}),
            ({"gpu": "..2"}, None, {"nvidia.com/gpu": 2}),
            ({"gpu": "1..2"}, {"nvidia.com/gpu": 1}, {"nvidia.com/gpu": 2}),
            ({"google.com/tpu": 8}, {"google.com/tpu": 8}, {"google.com/tpu": 8}),
            ({"amd.com/gpu": 0}, {"amd.com/gpu": 0}, {"amd.com/gpu": 0}),
        ):
            with self.subTest(resources=resources):
                authored = read_polyaxonfile(
                    {"container": {"image": "busybox:1.36"}, "resources": resources}
                )
                before = authored.to_dict()
                compiled = OperationSpecification.compile_operation(authored)
                expected = {}
                if requests:
                    expected["requests"] = requests
                if limits:
                    expected["limits"] = limits
                assert compiled.run.kind == "job"
                assert compiled.run.container.resources == expected
                assert authored.to_dict() == before
                replayed = read_polyaxonfile(authored.to_source_json())
                assert replayed.resources == resources

    def test_resources_rejects_invalid_values(self):
        for resources, message in (
            ({"cpu": ".."}, "resources.cpu needs a request"),
            ({"cpu": "4..2"}, "request greater than its limit"),
            ({"memory": "1Gi..512Mi"}, "request greater than its limit"),
            ({"memory": "1.9..1.1"}, "request greater than its limit"),
            ({"cpu": "1k"}, "unsupported value `1k`"),
            ({"memory": "400m"}, "unsupported value `400m`"),
            ({"memory": "1mi"}, "unsupported value `1mi`"),
            ({"cpu": "1_000"}, "unsupported value `1_000`"),
            ({"cpu": "1e3"}, "unsupported value `1e3`"),
            ({"cpu": "{{ params.cpu }}"}, "use container.resources"),
            ({"cpu": "١"}, "unsupported value `١`"),
            ({"memory": "١Gi"}, "unsupported value `١Gi`"),
            ({"gpu": "١"}, "unsupported value `١`"),
            ({"cpu": -1}, "finite non-negative"),
            ({"cpu": float("nan")}, "finite non-negative"),
            ({"memory": float("inf")}, "finite non-negative"),
            ({"cpu": True}, "number or a range"),
            ({"gpu": 1.5}, "integer count"),
            ({"gpu": "1.5"}, "unsupported value `1.5`"),
            ({"gpu": 10**400}, "resources.gpu is too large"),
            ({"gpu": "9" * 20}, "unsupported value `{}`".format("9" * 20)),
            ({"gpu": "1.." + "9" * 20}, "unsupported value `{}`".format("9" * 20)),
            ({"nvidia.com/gpu": 1}, "spelled gpu"),
            ({"cpus": 1}, "Unknown resource `cpus`"),
            ({"ephemeral-storage": "1Gi"}, "Unknown resource `ephemeral-storage`"),
            ({"hugepages-2Mi": "1Gi"}, "Unknown resource `hugepages-2Mi`"),
        ):
            with self.subTest(resources=resources):
                with self.assertRaisesRegex(ValidationError, re.escape(message)):
                    V1Polyaxonfile.from_dict({"resources": resources})
        for resources in ("cpu=1", ["cpu"]):
            with self.subTest(resources=resources), self.assertRaises(ValidationError):
                V1Polyaxonfile.from_dict({"resources": resources})

    def test_resources_units_agree_with_reporting_and_converters(self):
        for cpu in ("2", "0.5", "500m", ".5", "500u"):
            with self.subTest(cpu=cpu):
                V1Polyaxonfile.from_dict({"resources": {"cpu": cpu}})
                assert to_cpu_value(cpu) == float(parse_quantity(cpu))
        for memory in ("512", "1.5Gi", "1Ki", "1Mi", "1Gi", "1Ti", "1k", "1M", "1G"):
            with self.subTest(memory=memory):
                V1Polyaxonfile.from_dict({"resources": {"memory": memory}})
                assert to_memory_bytes(memory) == int(parse_quantity(memory))

        compiled = _compile({"container": {"image": "b"}, "resources": {"gpu": 2}})
        resources = compiled.run.container.resources
        assert requests_gpu(
            k8s_schemas.V1ResourceRequirements(
                requests=resources["requests"], limits=resources["limits"]
            )
        )

    def test_resources_merge_like_the_native_run_patch(self):
        base = {
            "run": {"kind": "job", "container": {"image": "base:v1"}},
            "resources": {"cpu": "2..8", "gpu": 1},
        }
        gpu = {"nvidia.com/gpu": 1}
        lowered = {"requests": {"cpu": 4, "memory": "1Gi"}}
        for strategy, expected in (
            (
                PatchStrategy.POST_MERGE,
                {
                    "requests": {"cpu": 4, "memory": "1Gi", **gpu},
                    "limits": {"cpu": "8", **gpu},
                },
            ),
            (
                PatchStrategy.PRE_MERGE,
                {
                    "requests": {"cpu": "2", "memory": "1Gi", **gpu},
                    "limits": {"cpu": "8", **gpu},
                },
            ),
            (PatchStrategy.REPLACE, lowered),
            (
                PatchStrategy.ISNULL,
                {"requests": {"cpu": "2", **gpu}, "limits": {"cpu": "8", **gpu}},
            ),
        ):
            with self.subTest(strategy=strategy):
                shortcut = _compile(
                    {
                        "patchStrategy": strategy,
                        "resources": {"cpu": 4, "memory": "1Gi"},
                        "component": base,
                    }
                )
                native = _compile(
                    {
                        "patchStrategy": strategy,
                        "runPatch": {"container": {"resources": deepcopy(lowered)}},
                        "component": base,
                    }
                )
                assert shortcut.run.container.resources == expected
                assert native.run.container.resources == expected

    def test_resources_with_same_layer_container_resources(self):
        native = {"requests": {"cpu": "1", "memory": "1Gi"}, "limits": {"cpu": "2"}}
        for strategy, expected in (
            (
                PatchStrategy.POST_MERGE,
                {"requests": {"cpu": "3", "memory": "1Gi"}, "limits": {"cpu": "2"}},
            ),
            (PatchStrategy.PRE_MERGE, native),
            (PatchStrategy.REPLACE, {"requests": {"cpu": "3"}}),
            (PatchStrategy.ISNULL, native),
        ):
            with self.subTest(strategy=strategy):
                compiled = _compile(
                    {
                        "patchStrategy": strategy,
                        "run": {"kind": "job", "container": {"image": "base:v1"}},
                        "container": {"resources": deepcopy(native)},
                        "resources": {"cpu": "3"},
                    }
                )
                assert compiled.run.container.resources == expected

    def test_resources_isolate_heterogeneous_replicas(self):
        # Replica patches share one payload natively; both spellings must isolate.
        native = {"container": {"resources": {"requests": {"cpu": "4"}}}}
        for strategy, source in product(
            PatchStrategy, ({"resources": {"cpu": "4"}}, {"runPatch": native})
        ):
            with self.subTest(strategy=strategy, source=source):
                compiled = _compile(
                    {
                        "patchStrategy": strategy,
                        **source,
                        "component": {
                            "run": {
                                "kind": "pytorchjob",
                                "master": {
                                    "replicas": 1,
                                    "container": {
                                        "image": "base:v1",
                                        "resources": {"requests": {"cpu": "2"}},
                                    },
                                },
                                "worker": {"replicas": 1},
                            }
                        },
                    }
                )
                master = compiled.run.master.container.resources
                worker = compiled.run.worker.container.resources
                assert worker == {"requests": {"cpu": "4"}}
                if strategy in (PatchStrategy.PRE_MERGE, PatchStrategy.ISNULL):
                    assert master == {"requests": {"cpu": "2"}}
                else:
                    assert master == {"requests": {"cpu": "4"}}
                # A later worker-only change must not reach the master.
                before = deepcopy(master)
                compiled.run.worker.container.resources["requests"]["cpu"] = "9"
                assert master == before

    def test_resources_reach_mpi_roles(self):
        replica = {
            "replicas": 1,
            "container": {"image": "base:v1", "resources": {"requests": {"cpu": "1"}}},
        }
        expected = {
            PatchStrategy.POST_MERGE: "4",
            PatchStrategy.PRE_MERGE: "1",
            PatchStrategy.REPLACE: "4",
            PatchStrategy.ISNULL: "1",
        }
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
                compiled = _compile(
                    {
                        "patchStrategy": strategy,
                        "resources": {"cpu": "4"},
                        "component": {
                            "run": {
                                "kind": "mpijob",
                                "launcher": deepcopy(replica),
                                "worker": deepcopy(replica),
                            }
                        },
                    }
                )
                for role in (compiled.run.launcher, compiled.run.worker):
                    assert role.container.resources == {
                        "requests": {"cpu": expected[strategy]}
                    }

    def test_resources_alone_empty_null_created_later_and_dags(self):
        compiled = _compile({"resources": {"cpu": "1"}})
        assert compiled.run.kind == "job"
        assert compiled.run.container.resources == {"requests": {"cpu": "1"}}

        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy, case="created later"):
                compiled = _compile(
                    {
                        "run": {"kind": "job"},
                        "patchStrategy": strategy,
                        "resources": {"cpu": "1"},
                        "runPatch": {"container": {"image": "busybox:1.36"}},
                    }
                )
                assert compiled.run.container.image == "busybox:1.36"
                assert compiled.run.container.resources == {"requests": {"cpu": "1"}}

        base = {
            "run": {
                "kind": "job",
                "container": {
                    "image": "base:v1",
                    "resources": {"requests": {"cpu": "1"}},
                },
            }
        }
        for strategy, expected in (
            (PatchStrategy.POST_MERGE, {"requests": {"cpu": "1"}}),
            (PatchStrategy.PRE_MERGE, {"requests": {"cpu": "1"}}),
            (PatchStrategy.REPLACE, {}),
            (PatchStrategy.ISNULL, {"requests": {"cpu": "1"}}),
        ):
            with self.subTest(strategy=strategy, case="empty"):
                compiled = _compile(
                    {"patchStrategy": strategy, "resources": {}, "component": base}
                )
                assert compiled.run.container.resources == expected

        authored = read_polyaxonfile({**deepcopy(base), "resources": {"cpu": "4"}})
        nulled = patch_polyaxonfile(authored.clone(), [{"resources": None}])
        for config in (nulled, read_polyaxonfile(nulled.to_source_json())):
            assert "resources" in config.model_fields_set
            assert config.resources is None
            compiled = OperationSpecification.compile_operation(config)
            assert compiled.run.container.resources == {"requests": {"cpu": "1"}}
        compiled = OperationSpecification.compile_operation(
            authored.clone(), override={"resources": None}
        )
        assert compiled.run.container.resources == {"requests": {"cpu": "1"}}

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
        compiled_dag = _compile(dag)
        for strategy in PatchStrategy:
            for resources in ({}, {"cpu": "1"}):
                with self.subTest(strategy=strategy, resources=resources):
                    authored = read_polyaxonfile(
                        {
                            **deepcopy(dag),
                            "patchStrategy": strategy,
                            "resources": resources,
                        }
                    )
                    with self.assertRaises(ValidationError):
                        OperationSpecification.compile_operation(authored)
                    with self.assertRaises(ValidationError):
                        CompiledOperationSpecification.apply_preset(
                            compiled_dag.clone(),
                            {"patchStrategy": strategy, "resources": resources},
                        )

    def test_resources_overlays_merge_by_key(self):
        base = {
            "container": {"image": "busybox:1.36"},
            "resources": {"gpu": 1, "cpu": "1"},
        }
        for strategy, expected in (
            (None, {"gpu": 2, "cpu": "1", "memory": "1Gi"}),
            (PatchStrategy.PRE_MERGE, {"gpu": 1, "cpu": "1", "memory": "1Gi"}),
            (PatchStrategy.REPLACE, {"gpu": 2, "memory": "1Gi"}),
            (PatchStrategy.ISNULL, {"gpu": 1, "cpu": "1"}),
        ):
            with self.subTest(strategy=strategy):
                overlay = {"resources": {"gpu": 2, "memory": "1Gi"}}
                if strategy:
                    overlay["patchStrategy"] = strategy
                config = patch_polyaxonfile(deepcopy(base), [overlay])
                assert config.resources == expected
                assert read_polyaxonfile(config.to_source_json()).resources == expected

    def test_resources_apply_in_named_presets(self):
        service = _compile(
            {
                "run": {
                    "kind": "service",
                    "ports": [8080],
                    "container": {
                        "image": "base:v1",
                        "resources": {"requests": {"cpu": "1"}},
                    },
                }
            }
        )
        kept = CompiledOperationSpecification.apply_preset(
            service.clone(),
            {"resources": {"cpu": "2", "gpu": 1}, "patchStrategy": "pre_merge"},
        )
        assert kept.run.container.resources == {
            "requests": {"cpu": "1", "nvidia.com/gpu": 1},
            "limits": {"nvidia.com/gpu": 1},
        }
        applied = CompiledOperationSpecification.apply_preset(
            service, {"resources": {"cpu": "2..4"}}
        )
        assert applied.run.kind == "service"
        assert applied.run.container.resources == {
            "requests": {"cpu": "2"},
            "limits": {"cpu": "4"},
        }

    def test_service_compiles_like_a_native_service(self):
        container = {"image": "busybox:1.36", "command": ["httpd"]}
        fields = {
            "ports": [8080, 9090],
            "rewritePath": True,
            "isExternal": False,
            "replicas": 2,
        }
        # Empty sections select a service; null expresses no service intent.
        for service, kind in (
            (fields, "service"),
            ({"ports": []}, "service"),
            ({}, "service"),
            (None, "job"),
        ):
            with self.subTest(service=service):
                authored = read_polyaxonfile(
                    {"container": container, "service": deepcopy(service)}
                )
                before = authored.to_dict()
                native = {"kind": kind, "container": container, **(service or {})}
                expected = _compile({"run": native}).run

                assert OperationSpecification.compile_operation(authored).run == (
                    expected
                )
                assert authored.to_dict() == before
                assert orjson_loads(authored.to_source_json())["service"] == service
                saved = read_polyaxonfile(authored.to_source_json())
                assert saved.to_dict() == before
                assert "run" not in saved.model_fields_set
        # Duplicates are kept, like native run.ports.
        compiled = _compile({"container": container, "service": {"ports": [8080] * 2}})
        assert compiled.run.ports == [8080, 8080]

    def test_service_validates_native_field_types(self):
        for service in (
            [8080],
            8080,
            {"ports": 8080},
            {"ports": "8080"},
            {"ports": ["8080"]},
            {"ports": [True]},
            {"ports": [8080.0]},
            {"ports": {"http": 8080}},
            {"rewritePath": "maybe"},
            {"isExternal": [True]},
            {"replicas": "2"},
            {"replicas": 1.5},
            # Only service fields: unknown and shared keys are rejected.
            {"port": 8080},
            {"kind": "service"},
            {"container": {"image": "busybox:1.36"}},
            {"cmd": "serve"},
            {"resources": {"cpu": 1}},
        ):
            with self.subTest(service=service), self.assertRaises(ValidationError):
                V1Polyaxonfile.from_dict({"service": service})
        refs = {
            "ports": "{{ ports }}",
            "rewritePath": "{{ rewrite }}",
            "isExternal": "{{ external }}",
            "replicas": "{{ replicas }}",
        }
        assert V1Polyaxonfile.from_dict({"service": refs}).service.to_dict() == refs
        # Root ports were replaced by the service section.
        with self.assertRaises(ValidationError):
            V1Polyaxonfile.from_dict({"ports": [8080]})

    def test_service_applies_between_run_and_run_patch(self):
        layer = {
            "run": {
                "kind": "service",
                "rewritePath": False,
                "container": {"image": "native:v1"},
            },
            "service": {"rewritePath": True},
        }
        assert _compile(layer).run.rewrite_path is True
        patched = {**layer, "runPatch": {"rewritePath": False}}
        assert _compile(patched).run.rewrite_path is False
        # Outer layers override inner ones regardless of spelling.
        outer = {"run": {"kind": "service", "rewritePath": False}, "component": layer}
        assert _compile(outer).run.rewrite_path is False

    def test_service_keeps_the_inherited_runtime_kind(self):
        service = {
            "run": {
                "kind": "service",
                "ports": [8080],
                "rewritePath": True,
                "container": {"image": "base:v1"},
            }
        }
        compiled = _compile(
            {"service": {"ports": [9090], "isExternal": True}, "component": service}
        )
        assert compiled.run.kind == "service"
        assert compiled.run.ports == [8080, 9090]
        assert compiled.run.rewrite_path is True
        assert compiled.run.is_external is True
        assert compiled.run.container.image == "base:v1"
        # Null fields add no native patch.
        compiled = _compile({"service": {"rewritePath": None}, "component": service})
        assert compiled.run.rewrite_path is True

        job = {"kind": "job", "container": {"image": "base:v1"}}
        replica = {"replicas": 1, "container": {"image": "base:v1"}}
        runs = (
            job,
            {"kind": "pytorchjob", "master": replica, "worker": replica},
            {
                "kind": "dag",
                "operations": [{"name": "first", "dagRef": "task"}],
                "components": [{"name": "task", "run": job}],
            },
        )
        # Empty sections still express service intent, so they conflict too.
        for section in ({"ports": [8080]}, {}):
            sources = [
                # A container-only inner layer already resolved to a job.
                {"service": section, "component": {"container": {"image": "base:v1"}}}
            ]
            for run in runs:
                sources.append({"run": run, "service": section})
                sources.append({"service": section, "component": {"run": run}})
            for source in sources:
                with self.subTest(source=source):
                    with self.assertRaises(PolyaxonValidationError) as error:
                        _compile(source)
                    assert "requires a service runtime" in str(error.exception)

    def test_service_merges_natively_per_strategy(self):
        native = {"kind": "service", "ports": [80, 8080], "rewritePath": True}
        section = {"ports": [8080, 9090], "isExternal": True}
        for strategy, same_layer, with_patch in (
            (PatchStrategy.POST_MERGE, [80, 8080, 9090], [80, 8080, 9090, 7070]),
            (PatchStrategy.PRE_MERGE, [8080, 9090, 80], [7070, 8080, 9090, 80]),
            (PatchStrategy.REPLACE, [8080, 9090], [7070]),
            (PatchStrategy.ISNULL, [80, 8080], [80, 8080]),
        ):
            with self.subTest(strategy=strategy):
                layer = {"patchStrategy": strategy, "run": native, "service": section}
                inherited = {
                    "patchStrategy": strategy,
                    "service": section,
                    "component": {"run": native},
                }
                for source in (layer, inherited):
                    compiled = _compile(source)
                    assert compiled.run.ports == same_layer
                    # Omitted fields keep their values; unset ones receive the section's.
                    assert compiled.run.rewrite_path is True
                    assert compiled.run.is_external is True
                # Explicit runPatch applies after the root shortcut.
                patched = {**layer, "runPatch": {"ports": [7070]}}
                assert _compile(patched).run.ports == with_patch

    def test_service_overlays_and_presets(self):
        base = {
            "container": {"image": "busybox:1.36"},
            "service": {"ports": [8080], "rewritePath": True},
        }
        for strategy, expected in (
            (None, [8080, 9090]),
            (PatchStrategy.PRE_MERGE, [9090, 8080]),
            (PatchStrategy.REPLACE, [9090]),
            (PatchStrategy.ISNULL, [8080]),
        ):
            with self.subTest(strategy=strategy):
                overlay = {"service": {"ports": [9090]}}
                if strategy:
                    overlay["patchStrategy"] = strategy
                config = patch_polyaxonfile(deepcopy(base), [overlay])
                replayed = read_polyaxonfile(config.to_source_json())
                compiled = OperationSpecification.compile_operation(replayed)
                assert compiled.run.kind == "service"
                for service in (config.service, replayed.service, compiled.run):
                    assert service.ports == expected
                    assert service.rewrite_path is True

        # Nested-model patching: a null section keeps the existing one.
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
                overlay = {"service": None, "patchStrategy": strategy}
                nulled = patch_polyaxonfile(deepcopy(base), [overlay])
                assert nulled.service.to_dict() == base["service"]
                compiled = OperationSpecification.compile_operation(nulled)
                assert compiled.run.kind == "service"
        # An explicit null field follows field patching.
        for strategy, expected in (
            (PatchStrategy.POST_MERGE, None),
            (PatchStrategy.PRE_MERGE, True),
            (PatchStrategy.REPLACE, None),
            (PatchStrategy.ISNULL, True),
        ):
            with self.subTest(strategy=strategy):
                overlay = {"service": {"rewritePath": None}, "patchStrategy": strategy}
                config = patch_polyaxonfile(deepcopy(base), [overlay])
                assert config.service.ports == [8080]
                assert config.service.rewrite_path is expected

        service = _compile(base)
        applied = CompiledOperationSpecification.apply_preset(
            service, {"service": {"ports": [9090], "isExternal": True}}
        )
        assert applied.run.ports == [8080, 9090]
        assert applied.run.rewrite_path is True
        assert applied.run.is_external is True
        job = _compile({"container": {"image": "busybox:1.36"}})
        for section in ({"ports": [9090]}, {}):
            with self.subTest(section=section):
                with self.assertRaises(PolyaxonValidationError):
                    CompiledOperationSpecification.apply_preset(
                        job, {"service": section}
                    )

    def test_service_cli_overlays_depend_on_the_file_kind(self):
        container = {"image": "busybox:1.36"}
        with tempfile.TemporaryDirectory() as directory:

            def write(name, content):
                path = os.path.join(directory, name)
                with open(path, "w") as f:
                    f.write(orjson_dumps(content))
                return path

            overlay = write("service.json", {"service": {"ports": [8080]}})
            kindless = write(
                "kindless.json",
                {"container": container, "service": {"rewritePath": True}},
            )
            component = write(
                "component.json", {"kind": "component", "container": container}
            )

            # A kindless file and its overlay form one layer.
            config = check_polyaxonfile(polyaxonfile=[kindless, overlay], is_cli=False)
            compiled = OperationSpecification.compile_operation(config)
            assert compiled.run.kind == "service"
            assert compiled.run.ports == [8080]
            assert compiled.run.rewrite_path is True

            # A component is wrapped first: its job is inherited by the overlay.
            with self.assertRaises(PolyaxonfileError) as error:
                check_polyaxonfile(polyaxonfile=[component, overlay], is_cli=False)
            assert isinstance(error.exception.__cause__, PolyaxonValidationError)
            assert "requires a service runtime" in str(error.exception.__cause__)

    def test_dag_compiles_like_a_native_dag(self):
        container = {"image": "busybox:1.36"}
        job = {"kind": "job", "container": container}
        fields = {
            "concurrency": 2,
            "earlyStopping": [{"kind": "failure_early_stopping", "percent": 50}],
            "components": [
                {
                    "name": "template",
                    "matrix": {
                        "kind": "grid",
                        "params": {"count": {"kind": "choice", "value": [1, 2]}},
                    },
                    "schedule": {"kind": "cron", "cron": "0 * * * *"},
                    "run": job,
                },
            ],
            "operations": [
                {"name": "prepare", "container": container, "cmd": "echo prepare"},
                {
                    "name": "once",
                    "dagRef": "template",
                    "dependencies": ["prepare"],
                    "matrix": None,
                    "schedule": None,
                },
                {"name": "inherited", "dagRef": "template"},
                {"name": "nested", "dag": {"operations": [{"name": "a", "run": job}]}},
            ],
        }
        shared = {
            "environment": {"nodeSelector": {"pool": "workers"}},
            "connections": ["artifacts"],
            "volumes": [{"name": "scratch", "emptyDir": {}}],
        }
        for section, root in ((fields, shared), ({}, {}), ({"operations": []}, {})):
            with self.subTest(section=section):
                authored = read_polyaxonfile({"dag": deepcopy(section), **root})
                before = authored.to_dict()
                expected = _compile({"run": {"kind": "dag", **section, **root}}).run

                assert OperationSpecification.compile_operation(authored).run == (
                    expected
                )
                assert compose_polyaxonfile(authored).dag is None
                assert authored.to_dict() == before
                assert orjson_loads(authored.to_source_json())["dag"] == section
                saved = read_polyaxonfile(authored.to_source_json())
                assert saved.to_dict() == before
                assert "run" not in saved.model_fields_set

        # Null expresses no DAG intent.
        compiled = _compile({"dag": None, "container": container})
        assert compiled.run.kind == "job"

        dag = CompiledOperationSpecification.apply_operation_contexts(
            _compile({"dag": fields})
        ).run
        assert dag.dag["once"].upstream == {"prepare"}
        assert dag.get_effective_op("prepare").run.kind == "job"
        assert dag.get_effective_op("once").matrix is None
        assert dag.get_effective_op("inherited").matrix.kind == "grid"
        assert dag.get_effective_op("nested").run.kind == "dag"

        typed = V1Operation(
            dag=V1DagShortcut(
                concurrency=2, operations=[{"name": "a", "container": container}]
            )
        )
        assert OperationSpecification.compile_operation(typed).run == (
            _compile({"run": {"kind": "dag", **typed.dag.to_dict()}}).run
        )

    def test_dag_validates_native_field_types(self):
        for dag in (
            [],
            "{{ dag }}",
            {"operations": {"name": "train"}},
            {"operations": [1]},
            {"components": "train"},
            {"concurrency": 0},
            {"concurrency": -1},
            {"earlyStopping": {"kind": "failure_early_stopping", "percent": 50}},
            # Only DAG fields: unknown and shared keys are rejected.
            {"ops": []},
            {"kind": "dag"},
            {"environment": {}},
            {"connections": []},
            {"volumes": []},
            {"container": {"image": "busybox:1.36"}},
            {"cmd": "train"},
            {"resources": {"cpu": 1}},
        ):
            with self.subTest(dag=dag), self.assertRaises(ValidationError):
                V1Polyaxonfile.from_dict({"dag": dag})
        refs = {
            "operations": "{{ operations }}",
            "components": "{{ components }}",
            "concurrency": "{{ concurrency }}",
            "earlyStopping": "{{ early_stopping }}",
        }
        assert V1Polyaxonfile.from_dict({"dag": refs}).dag.to_dict() == refs

    def test_dag_rejects_other_runtimes(self):
        job = {"kind": "job", "container": {"image": "base:v1"}}
        replica = {"replicas": 1, "container": {"image": "base:v1"}}
        runs = (
            job,
            {"kind": "service", "container": {"image": "base:v1"}},
            {"kind": "pytorchjob", "master": replica, "worker": replica},
        )
        # Empty sections still express DAG intent, so they conflict too.
        for section in ({"concurrency": 2}, {}):
            sources = [
                # A container-only inner layer already resolved to a job.
                {"dag": section, "component": {"container": {"image": "base:v1"}}}
            ]
            for run in runs:
                sources.append({"run": run, "dag": section})
                sources.append({"dag": section, "component": {"run": run}})
            for source in sources:
                with self.subTest(source=source):
                    with self.assertRaises(PolyaxonValidationError) as error:
                        _compile(source)
                    assert "requires a dag runtime" in str(error.exception)

        # dag applies first, so a service section meets the DAG it created.
        for source, expected in (
            ({"dag": {}, "service": {}}, "requires a service runtime"),
            ({"dag": {"concurrency": 2}, "service": {}}, "requires a service runtime"),
            ({"service": {}, "component": {"dag": {}}}, "requires a service runtime"),
            ({"dag": {}, "component": {"service": {}}}, "requires a dag runtime"),
        ):
            with self.subTest(source=source):
                with self.assertRaises(PolyaxonValidationError) as error:
                    _compile(source)
                assert expected in str(error.exception)

        # Parent fields never become implicit node defaults.
        for shortcut in (
            {"container": {"image": "busybox:1.36"}},
            {"cmd": "train"},
            {"env": {}},
            {"resources": {"cpu": 1}},
            {"init": [{"container": {"name": "a", "image": "busybox:1.36"}}]},
            {"sidecars": [{"name": "a", "image": "busybox:1.36"}]},
        ):
            with self.subTest(shortcut=shortcut):
                with self.assertRaises(ValidationError):
                    _compile({"dag": {}, **shortcut})

        with self.assertRaises(ValidationError) as error:
            get_shortcut_specification({"dag": {}}, None, sandbox=True)
        assert "plugins.sandbox is only supported" in str(error.exception)

    def test_dag_merges_natively_per_strategy(self):
        job = {"kind": "job", "container": {"image": "base:v1"}}
        native = {
            "kind": "dag",
            "concurrency": 2,
            "operations": [{"name": "first", "run": job}],
        }
        section = {"concurrency": 3, "operations": [{"name": "second", "run": job}]}
        run_patch = {"concurrency": 4, "operations": [{"name": "third", "run": job}]}

        def names(run):
            return [op.name for op in run.operations]

        for strategy, same_layer, with_patch in (
            (
                PatchStrategy.POST_MERGE,
                (3, ["first", "second"]),
                (4, ["first", "second", "third"]),
            ),
            (
                PatchStrategy.PRE_MERGE,
                (2, ["second", "first"]),
                (2, ["third", "second", "first"]),
            ),
            (PatchStrategy.REPLACE, (3, ["second"]), (4, ["third"])),
            (PatchStrategy.ISNULL, (2, ["first"]), (2, ["first"])),
        ):
            with self.subTest(strategy=strategy):
                layer = {"patchStrategy": strategy, "run": native, "dag": section}
                inherited = {
                    "patchStrategy": strategy,
                    "dag": section,
                    "component": {"run": native},
                }
                for source in (layer, inherited):
                    compiled = _compile(source).run
                    assert (compiled.concurrency, names(compiled)) == same_layer
                # Explicit runPatch applies after the root shortcut.
                compiled = _compile({**layer, "runPatch": run_patch}).run
                assert (compiled.concurrency, names(compiled)) == with_patch
                # Null fields add no native patch.
                compiled = _compile(
                    {
                        "patchStrategy": strategy,
                        "dag": {"concurrency": None},
                        "component": {"run": native},
                    }
                ).run
                assert compiled.concurrency == 2

        # Outer layers override inner ones regardless of spelling.
        outer = {
            "run": {"kind": "dag", "concurrency": 5},
            "component": {"dag": {"concurrency": 3}},
        }
        assert _compile(outer).run.concurrency == 5

    def test_dag_overlays_and_presets(self):
        job = {"kind": "job", "container": {"image": "base:v1"}}
        first, second = ({"name": name, "run": job} for name in ("first", "second"))
        base = {"dag": {"concurrency": 2, "operations": [first]}}
        for strategy, expected in (
            (None, ["first", "second"]),
            (PatchStrategy.PRE_MERGE, ["second", "first"]),
            (PatchStrategy.REPLACE, ["second"]),
            (PatchStrategy.ISNULL, ["first"]),
        ):
            with self.subTest(strategy=strategy):
                overlay = {"dag": {"operations": [second]}}
                if strategy:
                    overlay["patchStrategy"] = strategy
                config = patch_polyaxonfile(deepcopy(base), [overlay])
                replayed = read_polyaxonfile(config.to_source_json())
                compiled = OperationSpecification.compile_operation(replayed)
                assert compiled.run.kind == "dag"
                for section in (config.dag, replayed.dag, compiled.run):
                    assert [op.name for op in section.operations] == expected
                    assert section.concurrency == 2

        # Nested-model patching: a null section keeps the existing one.
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
                overlay = {"dag": None, "patchStrategy": strategy}
                nulled = patch_polyaxonfile(deepcopy(base), [overlay])
                assert nulled.dag.concurrency == 2
                assert _compile(base).run == (
                    OperationSpecification.compile_operation(nulled).run
                )
        # An explicit null field follows field patching.
        for strategy, expected in (
            (PatchStrategy.POST_MERGE, None),
            (PatchStrategy.PRE_MERGE, 2),
            (PatchStrategy.REPLACE, None),
            (PatchStrategy.ISNULL, 2),
        ):
            with self.subTest(strategy=strategy):
                overlay = {"dag": {"concurrency": None}, "patchStrategy": strategy}
                config = patch_polyaxonfile(deepcopy(base), [overlay])
                assert config.dag.concurrency == expected
                assert [op.name for op in config.dag.operations] == ["first"]
                compiled = OperationSpecification.compile_operation(config)
                assert compiled.run.concurrency == expected

        applied = CompiledOperationSpecification.apply_preset(
            _compile(base), {"dag": {"concurrency": 4, "operations": [second]}}
        )
        assert applied.run.concurrency == 4
        assert [op.name for op in applied.run.operations] == ["first", "second"]
        job_run = _compile({"container": {"image": "busybox:1.36"}})
        for section in ({"concurrency": 4}, {}):
            with self.subTest(section=section):
                with self.assertRaises(PolyaxonValidationError):
                    CompiledOperationSpecification.apply_preset(
                        job_run, {"dag": section}
                    )

    def test_runtime_fields_compile_like_native_run_fields(self):
        container = {"image": "busybox:1.36"}
        fields = {
            "environment": {
                "nodeSelector": {"pool": "workers"},
                "securityContext": {"runAsUser": 1000},
            },
            "init": [
                {
                    "container": {
                        "name": "setup",
                        "image": "busybox:1.36",
                        "volumeMounts": [{"name": "scratch", "mountPath": "/scratch"}],
                    }
                }
            ],
            "connections": ["artifacts"],
            "sidecars": [{"name": "metrics", "image": "busybox:1.36"}],
            "volumes": [{"name": "scratch", "emptyDir": {}}],
        }
        for kind in ("job", "service"):
            with self.subTest(kind=kind):
                native = {"kind": kind, "container": container, **deepcopy(fields)}
                compiled = _compile(
                    {"run": {"kind": kind}, "container": container, **fields}
                )
                assert compiled.run == _compile({"run": native}).run

        for field, value in fields.items():
            with self.subTest(field=field):
                authored = read_polyaxonfile({field: deepcopy(value)})
                before = authored.to_dict()
                compiled = OperationSpecification.compile_operation(authored)
                native = _compile({"run": {"kind": "job", field: deepcopy(value)}})
                assert compiled.run.kind == "job"
                assert compiled.run == native.run
                assert authored.to_dict() == before
                saved = authored.to_source_json()
                assert orjson_loads(saved)[field] == value
                assert read_polyaxonfile(saved).to_dict() == before

    def test_runtime_fields_patch_exactly_like_run_patch(self):
        role = {"container": {"image": "base:v1"}, **BASE_RUNTIME}
        replica = {"replicas": 1, **role}
        task = {"kind": "job", "container": {"image": "base:v1"}}
        runtimes = (
            {"kind": "job", **role},
            {"kind": "service", **role},
            {"kind": "pytorchjob", "master": replica, "worker": replica},
            {
                "kind": "dag",
                "operations": [{"name": "first", "dagRef": "task"}],
                "components": [{"name": "task", "run": task}],
            },
        )

        def compile_with(run, strategy, layer):
            return _compile(
                {"patchStrategy": strategy, **layer, "component": {"run": run}}
            )

        for run, field, strategy in product(runtimes, NEW_RUNTIME, PatchStrategy):
            with self.subTest(kind=run["kind"], field=field, strategy=strategy):
                value = NEW_RUNTIME[field]
                try:
                    expected = compile_with(run, strategy, {"runPatch": {field: value}})
                except ValidationError:
                    # Fields a runtime does not declare fail in both spellings.
                    with self.assertRaises(ValidationError):
                        compile_with(run, strategy, {field: value})
                    continue
                assert compile_with(run, strategy, {field: value}).run == expected.run

    def test_runtime_fields_merge_natively_per_strategy(self):
        def names(field, values):
            if field == "connections":
                return values
            if field == "init":
                return [value.container.name for value in values]
            return [value.name for value in values]

        for strategy, expected, pool in (
            (PatchStrategy.POST_MERGE, ["base", "new"], "new"),
            (PatchStrategy.PRE_MERGE, ["new", "base"], "base"),
            (PatchStrategy.REPLACE, ["new"], "new"),
            (PatchStrategy.ISNULL, ["base"], "base"),
        ):
            with self.subTest(strategy=strategy):
                run = _compile(
                    {
                        "patchStrategy": strategy,
                        **NEW_RUNTIME,
                        "component": {"run": {"kind": "job", **BASE_RUNTIME}},
                    }
                ).run
                for field in ("init", "connections", "sidecars", "volumes"):
                    assert names(field, getattr(run, field)) == expected
                # environment merges per field; unset fields are inherited.
                assert run.environment.node_selector == {"pool": pool}
                assert run.environment.labels == {"team": "a"}

    def test_runtime_fields_take_literal_values(self):
        for field in NEW_RUNTIME:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                V1Polyaxonfile.from_dict({field: "{{ params.value }}"})
        # Scalars and mappings fail validation instead of escaping as TypeError.
        for field, value in product(("sidecars", "volumes"), (True, 1, {"name": "a"})):
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValidationError):
                    V1Polyaxonfile.from_dict({field: value})
        with self.assertRaisesRegex(ValidationError, "environment"):
            V1Polyaxonfile.from_dict({"environment": {"nodeSelector": ["pool"]}})

        # Nested templates are kept and resolved like native values.
        authored = read_polyaxonfile(
            {
                "inputs": [{"name": "pool", "type": "str"}],
                "params": {"pool": {"value": "gpu"}},
                "container": {"image": "busybox:1.36"},
                "environment": {"nodeSelector": {"pool": "{{ pool }}"}},
            }
        )
        compiled = OperationSpecification.compile_operation(authored)
        assert compiled.run.environment.node_selector == {"pool": "{{ pool }}"}
        compiled.apply_params(params=authored.params)
        compiled = CompiledOperationSpecification.apply_operation_contexts(compiled)
        compiled = CompiledOperationSpecification.apply_runtime_contexts(compiled)
        assert compiled.run.environment.node_selector == {"pool": "gpu"}

    def test_env_shortcut_leaves_sidecar_env_untouched(self):
        compiled = _compile(
            {
                "container": {"image": "busybox:1.36"},
                "env": {"A": "1"},
                "sidecars": [
                    {
                        "name": "metrics",
                        "image": "busybox:1.36",
                        "env": [{"name": "B", "value": "2"}],
                    }
                ],
            }
        )
        assert _env(compiled.run.container) == [("A", "1", False)]
        assert _env(compiled.run.sidecars[0]) == [("B", "2", False)]

    def test_runtime_fields_overlays_and_presets(self):
        base = {"container": {"image": "busybox:1.36"}, **BASE_RUNTIME}
        for strategy, expected in (
            (None, ["base", "new"]),
            (PatchStrategy.PRE_MERGE, ["new", "base"]),
            (PatchStrategy.REPLACE, ["new"]),
            (PatchStrategy.ISNULL, ["base"]),
        ):
            with self.subTest(strategy=strategy):
                overlay = deepcopy(NEW_RUNTIME)
                if strategy:
                    overlay["patchStrategy"] = strategy
                config = patch_polyaxonfile(deepcopy(base), [overlay])
                assert config.connections == expected
                assert [sidecar.name for sidecar in config.sidecars] == expected
                replayed = read_polyaxonfile(config.to_source_json())
                compiled = OperationSpecification.compile_operation(replayed)
                assert [volume.name for volume in compiled.run.volumes] == expected

        # An explicit null clears an overlaid list under the default strategy.
        nulled = patch_polyaxonfile(
            deepcopy(base), [{"sidecars": None, "volumes": None}]
        )
        compiled = OperationSpecification.compile_operation(nulled)
        assert compiled.run.sidecars is None
        assert compiled.run.volumes is None

        job = _compile(base)
        applied = CompiledOperationSpecification.apply_preset(
            job, {"sidecars": NEW_RUNTIME["sidecars"]}
        )
        assert [sidecar.name for sidecar in applied.run.sidecars] == ["base", "new"]
        dag = _compile(
            {
                "run": {
                    "kind": "dag",
                    "operations": [{"name": "first", "dagRef": "task"}],
                    "components": [
                        {
                            "name": "task",
                            "run": {"kind": "job", "container": {"image": "b"}},
                        }
                    ],
                }
            }
        )
        with self.assertRaises(ValidationError):
            CompiledOperationSpecification.apply_preset(
                dag, {"init": NEW_RUNTIME["init"]}
            )

    def test_get_shortcuts_omits_only_none(self):
        assert get_shortcuts() is None
        # Empty and zero values are authored values; the model validates them.
        assert get_shortcuts(image="", cmd=[], env={}, cpu=0, gpu=0, ports=[]) == {
            "container": {"image": ""},
            "cmd": [],
            "env": {},
            "resources": {"cpu": 0, "gpu": 0},
            "service": {"ports": []},
        }

    def test_get_shortcuts_keeps_values_as_given(self):
        assert get_shortcuts(cmd="echo hello") == {"cmd": "echo hello"}
        assert get_shortcuts(cmd=["a", "b"], memory="512Mi..1Gi") == {
            "cmd": ["a", "b"],
            "resources": {"memory": "512Mi..1Gi"},
        }

    def test_sandbox_without_a_runtime_defaults_to_a_service(self):
        container = {"container": {"image": "python:3.12"}}
        with_ports = {**container, "service": {"ports": [8080]}}
        for content, shortcuts, expected in (
            (None, container, {}),
            (None, with_ports, {"ports": [8080]}),
            (container, None, {}),
            (with_ports, None, {"ports": [8080]}),
        ):
            with self.subTest(content=content, shortcuts=shortcuts):
                config = get_shortcut_specification(
                    deepcopy(content), deepcopy(shortcuts), sandbox=True
                )
                assert orjson_loads(config.to_source_json())["service"] == expected
                compiled = OperationSpecification.compile_operation(config)
                assert compiled.run.kind == "service"
                assert compiled.plugins.sandbox is True

    def test_validate_shortcuts_rejects_other_keys(self):
        validate_shortcuts({key: None for key in SHORTCUT_KEYS})
        # Preset validation alone accepts these keys.
        for key in ("name", "plugins", "runPatch"):
            with self.subTest(key=key), self.assertRaises(PolyaxonfileError):
                validate_shortcuts({key: None})

        with patch("polyaxon._config.spec.ConfigSpec.read_from_url") as read_from_url:
            with self.assertRaises(PolyaxonfileError) as error:
                check_polyaxonfile(
                    url="https://example.com/polyaxonfile.yaml",
                    shortcuts={"name": "inline"},
                    is_cli=False,
                )
        assert "name" in str(error.exception.__cause__)
        read_from_url.assert_not_called()
