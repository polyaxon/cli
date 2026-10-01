from copy import deepcopy
import pytest

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
