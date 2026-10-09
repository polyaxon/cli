from copy import deepcopy
import pytest
from unittest.mock import patch

from clipped.utils.json import orjson_loads
from polyaxon._flow.polyaxonfile import V1Component, V1Operation
from polyaxon._flow.run.dag import V1Dag
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
    compose_polyaxonfile,
    read_polyaxonfile,
)
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonfileError, PolyaxonSchemaError


@pytest.mark.polyaxonfile_mark
class TestSharedDags(BaseTestCase):
    @staticmethod
    def _prepare(source):
        compiled = OperationSpecification.compile_operation(read_polyaxonfile(source))
        return CompiledOperationSpecification.apply_operation_contexts(compiled).run

    def test_direct_embedded_and_referenced_nodes_keep_authored_kinds(self):
        job = {"kind": "job", "container": {"image": "busybox:1.36"}}
        for kind in (None, "component", "operation"):
            with self.subTest(kind=kind):
                template = {
                    "name": "template",
                    "params": {"count": 3},
                    "inputs": [{"name": "count", "type": "int"}],
                    "run": job,
                }
                if kind:
                    template["kind"] = kind
                nodes = [
                    {
                        "name": "direct",
                        "outputs": [{"name": "result", "type": "int"}],
                        "run": job,
                    },
                    {
                        "name": "embedded",
                        "component": template,
                        "dependencies": ["direct"],
                    },
                    {
                        "name": "referenced",
                        "dagRef": "template",
                        "params": {
                            "count": {"ref": "ops.direct", "value": "outputs.result"}
                        },
                    },
                ]
                if kind:
                    for node in nodes:
                        node["kind"] = kind
                source = {
                    "run": {
                        "kind": "dag",
                        "components": [template],
                        "operations": nodes,
                    }
                }
                authored = read_polyaxonfile(source)
                before = authored.to_dict()

                dag = self._prepare(authored)

                assert set(dag.dag) == {"direct", "embedded", "referenced"}
                assert dag.dag["direct"].downstream == {"embedded", "referenced"}
                assert dag.dag["embedded"].upstream == {"direct"}
                assert dag.dag["referenced"].upstream == {"direct"}
                assert dag.get_effective_op("embedded").params["count"].value == 3
                for name in dag.dag:
                    dag.set_op_component(name)
                    child = dag.get_op_spec_by_name(name)
                    assert child.kind == kind
                    assert child.name == name
                    compiled = OperationSpecification.compile_operation(
                        child, is_dag_node=True
                    )
                    assert compiled.name == name
                    assert compiled.run.container.image == "busybox:1.36"
                assert dag.get_op_spec_by_index(2).dag_ref == "template"
                assert authored.to_dict() == before
                assert read_polyaxonfile(authored.to_json()).to_dict() == before

    def test_compiled_dag_preserves_explicit_nulls_in_definitions(self):
        for nested in (False, True):
            with self.subTest(nested=nested):
                source_dag = {
                    "kind": "dag",
                    "concurrency": None,
                    "environment": None,
                    "components": [
                        {
                            "kind": "component",
                            "name": "train",
                            "matrix": {
                                "kind": "grid",
                                "params": {
                                    "count": {"kind": "choice", "value": [1, 2]}
                                },
                            },
                            "schedule": {"kind": "cron", "cron": "0 * * * *"},
                            "run": {
                                "kind": "job",
                                "container": {"image": "busybox:1.36"},
                            },
                        },
                        {
                            "kind": "operation",
                            "name": "single",
                            "dagRef": "train",
                            "matrix": None,
                            "schedule": None,
                            "queue": None,
                        },
                    ],
                    "operations": [
                        {
                            "kind": "operation",
                            "name": "once",
                            "dagRef": "train",
                            "matrix": None,
                            "schedule": None,
                        },
                        {"name": "from-template", "dagRef": "single"},
                        {"name": "inherited", "dagRef": "train"},
                    ],
                }
                source = {"queue": None, "schedule": None, "run": source_dag}
                if nested:
                    source["run"] = {
                        "kind": "dag",
                        "concurrency": None,
                        "environment": None,
                        "operations": [{"name": "nested", "run": source_dag}],
                    }
                authored = read_polyaxonfile(source)
                before = authored.to_dict(exclude_none=False)
                compiled = OperationSpecification.compile_operation(authored)

                content = compiled.to_json()
                assert content == compiled.to_json()
                saved = orjson_loads(content)
                restored = CompiledOperationSpecification.read(content)
                assert orjson_loads(restored.to_json()) == saved
                dag = CompiledOperationSpecification.apply_operation_contexts(
                    restored
                ).run
                definitions = saved["run"]
                if nested:
                    definitions = definitions["operations"][0]["run"]
                    child = OperationSpecification.compile_operation(
                        dag.get_op_spec_by_name("nested"), is_dag_node=True
                    )
                    child = CompiledOperationSpecification.read(child.to_json())
                    dag = CompiledOperationSpecification.apply_operation_contexts(
                        child
                    ).run

                assert dag.get_effective_op("once").matrix is None
                assert dag.get_effective_op("from-template").matrix is None
                assert dag.get_effective_op("inherited").matrix.kind == "grid"
                for field in ("operations", "components"):
                    assert definitions[field] == source_dag[field]
                assert "queue" not in saved
                assert "schedule" not in saved
                assert saved["run"]["concurrency"] is None
                assert saved["run"]["environment"] is None
                assert "matrix" not in saved
                assert "queue" not in definitions["operations"][0]
                assert authored.to_dict(exclude_none=False) == before
                serialized = authored.to_dict()["run"]
                if nested:
                    serialized = serialized["operations"][0]["run"]
                assert serialized == source_dag

    def test_compiled_serialization_preserves_explicit_dag_nulls(self):
        for kind in ("job", "service", "dag"):
            with self.subTest(kind=kind):
                run = {"kind": kind, "environment": None}
                expected_run = {"kind": kind}
                if kind == "dag":
                    run.update(
                        {"operations": None, "components": None, "concurrency": None}
                    )
                    expected_run.update(
                        {
                            "environment": None,
                            "operations": None,
                            "components": None,
                            "concurrency": None,
                        }
                    )
                else:
                    run["container"] = {"image": "busybox:1.36"}
                    expected_run["container"] = run["container"]
                compiled = CompiledOperationSpecification.read(
                    {
                        "kind": "compiled_operation",
                        "queue": None,
                        "schedule": None,
                        "matrix": None,
                        "run": run,
                    }
                )
                expected = {"kind": "compiled_operation", "run": expected_run}

                assert compiled.to_dict() == expected
                assert orjson_loads(compiled.to_json()) == expected
                assert orjson_loads(compiled.to_json()) == expected
                restored = CompiledOperationSpecification.read(compiled.to_json())
                assert orjson_loads(restored.to_json()) == expected
                explicit = compiled.to_dict(exclude_none=False)
                for field in ("queue", "schedule", "matrix"):
                    assert explicit[field] is None
                assert explicit["run"]["environment"] is None

    def test_compiled_dag_keeps_omitted_fields_absent(self):
        source = {"kind": "compiled_operation", "run": {"kind": "dag"}}

        compiled = CompiledOperationSpecification.read(source)

        assert compiled.to_dict() == source
        assert orjson_loads(compiled.to_json()) == source
        assert orjson_loads(compiled.to_json()) == source

    def test_compiled_dag_keeps_templated_definitions(self):
        source = {
            "kind": "compiled_operation",
            "run": {
                "kind": "dag",
                "operations": "{{ operations }}",
                "components": "{{ components }}",
            },
        }

        compiled = CompiledOperationSpecification.read(source)

        assert orjson_loads(compiled.to_json()) == source
        restored = CompiledOperationSpecification.read(compiled.to_json())
        assert orjson_loads(restored.to_json()) == source

    def test_compiled_serialization_retains_deferred_execution_fields(self):
        source = {
            "kind": "compiled_operation",
            "inputs": [
                {"name": "count", "type": "int", "value": 3, "isOptional": True}
            ],
            "outputs": [{"name": "result", "type": "int"}],
            "contexts": [
                {"name": "offset", "type": "int", "value": 3, "isOptional": True}
            ],
            "strictParams": False,
            "matrix": {
                "kind": "grid",
                "params": {"seed": {"kind": "choice", "value": [1, 2]}},
            },
            "schedule": {"kind": "cron", "cron": "0 * * * *"},
            "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
        }
        compiled = CompiledOperationSpecification.read(source)

        content = compiled.to_json()
        assert orjson_loads(content) == source
        assert content == compiled.to_json()
        restored = CompiledOperationSpecification.read(content)
        assert orjson_loads(restored.to_json()) == source

    def test_compiled_serialization_does_not_mutate_definitions(self):
        source = {
            "kind": "compiled_operation",
            "run": {
                "kind": "dag",
                "environment": None,
                "concurrency": None,
                "components": [
                    {
                        "kind": "component",
                        "name": "train",
                        "queue": None,
                        "params": {
                            "options": {"value": {"items": [1, {"value": None}]}}
                        },
                        "run": {
                            "kind": "job",
                            "container": {
                                "image": "busybox:1.36",
                                "args": ["{{ options }}"],
                            },
                        },
                    }
                ],
                "operations": [
                    {
                        "kind": "operation",
                        "name": "once",
                        "dagRef": "train",
                        "schedule": None,
                        "matrix": None,
                    }
                ],
            },
        }
        compiled = CompiledOperationSpecification.read({**source, "queue": None})
        template = compiled.run.components[0]
        node = compiled.run.operations[0]
        models = (
            compiled,
            compiled.run,
            template,
            template.run,
            template.params["options"],
            node,
        )
        fields_sets = [model.model_fields_set.copy() for model in models]
        before = compiled.to_dict(exclude_none=False)

        assert orjson_loads(compiled.to_json()) == source

        assert compiled.to_dict(exclude_none=False) == before
        assert [model.model_fields_set for model in models] == fields_sets
        assert compiled.run.dag == {}

    def test_compiled_serializer_visits_each_definition_once(self):
        job = {"kind": "job", "container": {"image": "busybox:1.36"}}
        source = {
            "kind": "compiled_operation",
            "run": {
                "kind": "dag",
                "components": [{"kind": "component", "name": "train", "run": job}],
                "operations": [
                    {
                        "kind": "operation",
                        "name": "once",
                        "dagRef": "train",
                        "schedule": None,
                    },
                    {
                        "kind": "operation",
                        "name": "nested",
                        "run": {
                            "kind": "dag",
                            "components": [
                                {"kind": "component", "name": "inner", "run": job}
                            ],
                            "operations": [
                                {
                                    "kind": "operation",
                                    "name": "inner-once",
                                    "dagRef": "inner",
                                    "matrix": None,
                                }
                            ],
                        },
                    },
                ],
            },
        }
        compiled = CompiledOperationSpecification.read(source)

        with patch.object(
            V1Operation, "obj_to_dict", wraps=V1Operation.obj_to_dict
        ) as operation_dump:
            with patch.object(
                V1Component, "obj_to_dict", wraps=V1Component.obj_to_dict
            ) as component_dump:
                with patch.object(
                    V1Dag, "obj_to_dict", wraps=V1Dag.obj_to_dict
                ) as dag_dump:
                    payload = orjson_loads(compiled.to_json())

        assert payload == source
        assert operation_dump.call_count == 3
        assert component_dump.call_count == 2
        assert dag_dump.call_count == 2
        dag_dump.assert_any_call(compiled.run, exclude_none=True)
        dag_dump.assert_any_call(compiled.run.operations[1].run, exclude_none=False)

    def test_unused_template_does_not_add_nodes_or_edges(self):
        job = {"kind": "job", "container": {"image": "busybox:1.36"}}
        source = {
            "run": {
                "kind": "dag",
                "components": [
                    {
                        "name": "unused",
                        "params": {
                            "result": {"ref": "ops.missing", "value": "outputs.result"}
                        },
                        "dependencies": ["also-missing"],
                        "run": job,
                    }
                ],
                "operations": [{"name": "train", "run": job}],
            }
        }

        dag = self._prepare(source)

        assert set(dag.dag) == {"train"}
        assert dag.dag["train"].upstream == set()
        assert dag.dag["train"].downstream == set()

    def test_template_params_create_edges_but_template_graph_fields_do_not(self):
        source = {
            "run": {
                "kind": "dag",
                "components": [
                    {
                        "name": "template",
                        "dependencies": ["not-a-node"],
                        "trigger": "all_failed",
                        "conditions": "{{ False }}",
                        "skipOnUpstreamSkip": True,
                        "joins": [
                            {
                                "query": "status:succeeded",
                                "params": {
                                    "unused": {
                                        "value": "outputs.value",
                                        "contextOnly": True,
                                    }
                                },
                            }
                        ],
                        "schedule": {"kind": "cron", "cron": "0 * * * *"},
                        "inputs": [{"name": "result", "type": "int"}],
                        "params": {
                            "result": {"ref": "ops.producer", "value": "outputs.result"}
                        },
                        "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
                    }
                ],
                "operations": [
                    {
                        "name": "consumer",
                        "dagRef": "template",
                        "patchStrategy": "pre_merge",
                    },
                    {
                        "name": "producer",
                        "outputs": [{"name": "result", "type": "int"}],
                        "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
                    },
                ],
            }
        }

        dag = self._prepare(source)

        assert dag.sort_topologically() == [["producer"], ["consumer"]]
        effective = dag.get_effective_op("consumer")
        assert effective.name == "consumer"
        assert effective.params["result"].ref == "ops.producer"
        assert effective.dependencies is None
        assert effective.conditions is None
        assert effective.joins is None
        assert effective.trigger is None
        assert effective.skip_on_upstream_skip is None
        assert effective.schedule is None
        child = dag.get_op_spec_by_name("consumer")
        assert child.component.schedule is not None
        assert child.component.dependencies == ["not-a-node"]
        standalone = compose_polyaxonfile(child)
        assert standalone.schedule is not None
        assert standalone.dependencies == ["not-a-node"]

    def test_node_graph_fields_win_independently_of_patch_strategy(self):
        for strategy in ("post_merge", "pre_merge", "replace", "isnull"):
            with self.subTest(strategy=strategy):
                source = {
                    "name": "node",
                    "patchStrategy": strategy,
                    "dependencies": ["prepare"],
                    "trigger": "all_succeeded",
                    "conditions": "{{ True }}",
                    "skipOnUpstreamSkip": False,
                    "joins": [
                        {
                            "query": "status:succeeded",
                            "params": {
                                "score": {"value": "outputs.score", "contextOnly": True}
                            },
                        }
                    ],
                    "component": {
                        "name": "template",
                        "dependencies": ["wrong"],
                        "trigger": "all_failed",
                        "conditions": "{{ False }}",
                        "skipOnUpstreamSkip": True,
                        "schedule": {"kind": "cron", "cron": "0 * * * *"},
                        "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
                    },
                }
                authored = read_polyaxonfile(source)
                before = authored.to_dict()

                compiled = OperationSpecification.compile_operation(
                    authored, is_dag_node=True
                )

                assert compiled.name == "node"
                assert compiled.dependencies == ["prepare"]
                assert compiled.trigger == "all_succeeded"
                assert compiled.conditions == "{{ True }}"
                assert compiled.skip_on_upstream_skip is False
                assert compiled.joins == authored.joins
                assert compiled.schedule is None
                assert compiled.contexts[0].name == "score"
                assert authored.to_dict() == before

    def test_nested_templates_inherit_matrix_and_copy_each_invocation(self):
        source = {
            "run": {
                "kind": "dag",
                "components": [
                    {
                        "kind": "operation",
                        "name": "base",
                        "inputs": [{"name": "seed", "type": "int"}],
                        "matrix": {
                            "kind": "grid",
                            "params": {"seed": {"kind": "choice", "value": [1, 2]}},
                        },
                        "run": {"kind": "job", "container": {"image": "base:v1"}},
                    },
                    {
                        "name": "wrapper",
                        "dagRef": "base",
                        "params": {"message": "hello"},
                    },
                ],
                "operations": [
                    {
                        "name": "first",
                        "dagRef": "wrapper",
                        "run": {"kind": "job", "container": {"image": "local:v2"}},
                    },
                    {"name": "second", "dagRef": "wrapper"},
                ],
            }
        }
        dag = self._prepare(source)
        assert dag.get_effective_op("first").run.container.image == "local:v2"
        assert dag.get_effective_op("second").run.container.image == "base:v1"
        assert dag.get_effective_op("first").matrix.kind == "grid"
        assert dag.get_effective_op("second").params["message"].value == "hello"
        first_effective = dag.get_effective_op("first")
        first_effective.run.container.image = "changed:v3"
        first_effective.params["message"].value = "changed"
        first_effective.matrix.params["seed"].value.append(3)
        second_effective = dag.get_effective_op("second")
        assert second_effective.run.container.image == "base:v1"
        assert second_effective.params["message"].value == "hello"
        assert second_effective.matrix.params["seed"].value == [1, 2]
        assert dag.components[0].run.container.image == "base:v1"
        assert dag.components[0].matrix.params["seed"].value == [1, 2]
        assert dag.components[1].params["message"].value == "hello"
        first = dag.get_op_spec_by_name("first")
        first.component.params["message"].value = "changed"
        second = dag.get_op_spec_by_name("second")
        assert second.component.params["message"].value == "hello"
        assert dag.components[1].component is None

    def test_invalid_nodes_and_template_cycles_fail_with_node_name(self):
        job = {"kind": "job", "container": {"image": "busybox:1.36"}}
        cases = [
            (
                [
                    {
                        "name": "train",
                        "run": job,
                        "schedule": {"kind": "cron", "cron": "0 * * * *"},
                    }
                ],
                [],
                "train.*schedule",
            ),
            (
                [{"name": "train", "run": job}, {"name": "train", "run": job}],
                [],
                "same name `train`",
            ),
            ([{"run": job}], [], "requires a name"),
            (
                [{"name": "train", "params": {"count": 1}}],
                [],
                "no definition field `train`",
            ),
            ([{"name": "train", "dagRef": "missing"}], [], "train.*missing"),
            (
                [{"name": "train", "dagRef": "a"}],
                [{"name": "a", "dagRef": "b"}, {"name": "b", "dagRef": "a"}],
                "train.*cycle.*a -> b -> a",
            ),
        ]
        for operations, components, error in cases:
            with self.subTest(error=error):
                with self.assertRaisesRegex(
                    (PolyaxonSchemaError, PolyaxonfileError), error
                ):
                    self._prepare(
                        {
                            "run": {
                                "kind": "dag",
                                "operations": deepcopy(operations),
                                "components": components,
                            }
                        }
                    )

    def test_graph_uses_params_selected_by_patch_strategy(self):
        dag = self._prepare(
            {
                "run": {
                    "kind": "dag",
                    "operations": [
                        {
                            "name": "train",
                            "patchStrategy": "pre_merge",
                            "params": {
                                "count": {
                                    "ref": "ops.missing",
                                    "value": "outputs.count",
                                }
                            },
                            "component": {
                                "params": {"count": 3},
                                "run": {
                                    "kind": "job",
                                    "container": {"image": "busybox:1.36"},
                                },
                            },
                        }
                    ],
                }
            }
        )

        assert set(dag.dag) == {"train"}
        assert dag.dag["train"].upstream == set()
        assert dag.get_effective_op("train").params["count"].value == 3

    def test_inherited_params_cannot_hide_orphan_or_cyclic_edges(self):
        for ref, error in (("ops.missing", "orphan"), ("ops.train", "acyclic")):
            with self.subTest(ref=ref):
                with self.assertRaisesRegex(PolyaxonSchemaError, error):
                    self._prepare(
                        {
                            "run": {
                                "kind": "dag",
                                "operations": [
                                    {
                                        "name": "train",
                                        "component": {
                                            "params": {
                                                "status": {
                                                    "ref": ref,
                                                    "value": "globals.status",
                                                }
                                            },
                                            "run": {
                                                "kind": "job",
                                                "container": {"image": "busybox:1.36"},
                                            },
                                        },
                                    }
                                ],
                            }
                        }
                    )
