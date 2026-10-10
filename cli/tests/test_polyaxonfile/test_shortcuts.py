from copy import deepcopy
import pytest
import subprocess

from clipped.compact.pydantic import ValidationError
from clipped.config.patch_strategy import PatchStrategy
from polyaxon._flow.polyaxonfile import V1Polyaxonfile, _dedupe_env
from polyaxon._k8s import k8s_schemas
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
    get_specification,
    patch_polyaxonfile,
    read_polyaxonfile,
)
from polyaxon._utils.test_utils import BaseTestCase


SECRET = {"secretKeyRef": {"name": "secrets", "key": "token"}}


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

    def test_env_targets_only_native_patch_roles(self):
        # MPI does not receive native runPatch container fields (#1431); env
        # must not reach it under any strategy either.
        replica = {
            "replicas": 1,
            "container": {"image": "base:v1", "env": [{"name": "A", "value": "1"}]},
        }
        for strategy in PatchStrategy:
            with self.subTest(strategy=strategy):
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
                    assert _env(role.container) == [("A", "1", False)]

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
