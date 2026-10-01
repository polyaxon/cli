from mock import call, patch
from pathlib import Path
import pytest
from tempfile import TemporaryDirectory

from clipped.compact.pydantic import ValidationError
from clipped.config.patch_strategy import PatchStrategy
from polyaxon._config.spec import ConfigSpec
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
    read_polyaxonfile,
)
from polyaxon._polyaxonfile.check import collect_references
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonfileError, PolyaxonSchemaError


@pytest.mark.polyaxonfile_mark
class TestSharedReferences(BaseTestCase):
    def test_kindless_run_in_partial_or_preset_can_wait_for_a_base(self):
        source = {"run": {"container": {"image": "local:v2"}}}
        for options in ({"partial": True}, {"is_preset": True}):
            with self.subTest(options=options):
                config = read_polyaxonfile(source, **options)

                assert config.run == source["run"]
                assert config.get_native_run() is None
                assert config.to_dict()["run"] == source["run"]

    def test_kindless_reference_patch_survives_serialization_before_collection(self):
        for field, ref in (
            ("pathRef", "./base.yaml"),
            ("urlRef", "https://example.com/base.yaml"),
            ("hubRef", "train:v1"),
            ("dagRef", "train"),
        ):
            with self.subTest(field=field):
                source = {
                    field: ref,
                    "run": {"container": {"image": "local:v2", "args": None}},
                }
                config = read_polyaxonfile(source)

                assert config.run == source["run"]
                assert config.get_run_kind() is None
                assert config.get_native_run() is None
                payload = config.to_dict(exclude_none=False)
                assert payload == source
                restored = read_polyaxonfile(config.to_json(exclude_none=False))
                assert restored.run == source["run"]
                payload["run"]["container"]["image"] = "changed:v3"
                assert config.run["container"]["image"] == "local:v2"

    def test_explicit_runtime_kind_cannot_fall_back_to_an_unvalidated_mapping(self):
        for run in (
            {"kind": "unknown"},
            {"kind": None},
            {"kind": "job", "ports": [8080]},
            {"kind": "pytorchjob", "container": {"image": "invalid:v1"}},
        ):
            with self.subTest(run=run), self.assertRaises(ValidationError):
                read_polyaxonfile({"hubRef": "train:v1", "run": run})

    @patch.object(ConfigSpec, "read_from_url")
    def test_local_patch_is_validated_against_the_resolved_runtime(self, read_url):
        read_url.return_value = {
            "run": {"kind": "job", "container": {"image": "base:v1"}},
        }
        config = read_polyaxonfile(
            {"urlRef": "https://example.com/base.yaml", "run": {"ports": [8080]}}
        )
        read_url.assert_not_called()

        collect_references(config)
        with self.assertRaises(ValidationError):
            OperationSpecification.compile_operation(config)

        replacement = read_polyaxonfile(
            {
                "urlRef": "https://example.com/base.yaml",
                "run": {"kind": "service", "ports": [8080]},
            }
        )
        collect_references(replacement)
        compiled = OperationSpecification.compile_operation(replacement)
        assert compiled.run.kind == "service"
        assert compiled.run.ports == [8080]

    @patch.object(ConfigSpec, "read_from_url")
    def test_reference_without_a_runtime_does_not_supply_a_guessed_kind(self, read_url):
        with self.assertRaisesRegex(ValidationError, "run.kind must be provided"):
            read_polyaxonfile({"run": {"container": {"image": "local:v2"}}})

        read_url.return_value = {"params": {"count": 3}}
        config = read_polyaxonfile(
            {
                "urlRef": "https://example.com/base.yaml",
                "run": {"container": {"image": "local:v2"}},
            }
        )
        collect_references(config)

        with self.assertRaisesRegex(PolyaxonSchemaError, "run.kind must be provided"):
            OperationSpecification.compile_operation(config)

    @patch.object(ConfigSpec, "read_from_url")
    def test_deferred_patch_and_null_keep_each_strategy_after_collection(
        self, read_url
    ):
        read_url.return_value = {
            "run": {"kind": "job", "container": {"image": "base:v1"}},
        }
        for strategy in (None, *PatchStrategy):
            for run in ({"container": {"image": "local:v2"}}, None):
                with self.subTest(strategy=strategy, run=run):
                    source = {"urlRef": "https://example.com/base.yaml", "run": run}
                    if strategy:
                        source["patchStrategy"] = strategy
                    config = read_polyaxonfile(source)
                    collect_references(config)
                    stored = config.to_dict(exclude_none=False)
                    local_wins = strategy in (
                        None,
                        PatchStrategy.POST_MERGE,
                        PatchStrategy.REPLACE,
                    )
                    if run is None:
                        assert stored["run"] is None
                    if run is None and local_wins:
                        with self.assertRaisesRegex(
                            PolyaxonSchemaError, "resolved Polyaxonfile has no run"
                        ):
                            OperationSpecification.compile_operation(config)
                    else:
                        compiled = OperationSpecification.compile_operation(config)
                        assert compiled.run.container.image == (
                            "local:v2" if run is not None and local_wins else "base:v1"
                        )

    def test_dag_reference_supplies_kind_before_node_validation(self):
        source = {
            "run": {
                "kind": "dag",
                "components": [
                    {
                        "name": "serve",
                        "run": {
                            "kind": "service",
                            "ports": [8080],
                            "container": {"image": "base:v1"},
                        },
                    }
                ],
                "operations": [
                    {
                        "name": "first",
                        "dagRef": "serve",
                        "run": {"container": {"image": "local:v2"}},
                    }
                ],
            }
        }
        config = read_polyaxonfile(source)
        compiled = OperationSpecification.compile_operation(config)

        CompiledOperationSpecification.apply_operation_contexts(compiled)

        node = compiled.run.get_effective_op("first")
        assert node.run.kind == "service"
        assert node.run.ports == [8080]
        assert node.run.container.image == "local:v2"
        assert config.run.operations[0].run == source["run"]["operations"][0]["run"]

    @patch.object(ConfigSpec, "read_from_url")
    def test_kindless_run_matches_job_service_and_replica_run_patches(self, read_url):
        container = {"image": "base:v1", "command": ["sh", "-c"]}
        replica = {"replicas": 2, "container": container}
        runtimes = (
            {"kind": "job", "container": container},
            {"kind": "service", "ports": [8080], "container": container},
            {"kind": "pytorchjob", "worker": replica},
            {"kind": "tfjob", "worker": replica},
            {"kind": "daskcluster", "worker": replica},
            {
                "kind": "raycluster",
                "head": {"container": container},
                "workers": {"small": replica},
            },
        )
        local_run = {"container": {"image": "local:v2"}}
        for runtime in runtimes:
            for strategy in PatchStrategy:
                with self.subTest(kind=runtime["kind"], strategy=strategy):
                    read_url.return_value = {"run": runtime}
                    config = read_polyaxonfile(
                        {
                            "urlRef": "https://example.com/base.yaml",
                            "run": local_run,
                            "patchStrategy": strategy,
                        }
                    )
                    collect_references(config)

                    compiled = OperationSpecification.compile_operation(config)
                    legacy = OperationSpecification.compile_operation(
                        read_polyaxonfile(
                            {
                                "component": {"run": runtime},
                                "runPatch": local_run,
                                "patchStrategy": strategy,
                            }
                        )
                    )

                    assert compiled.run.to_dict() == legacy.run.to_dict()
                    assert compiled.run.kind == runtime["kind"]
                    image = (
                        "local:v2"
                        if strategy
                        in (
                            PatchStrategy.POST_MERGE,
                            PatchStrategy.REPLACE,
                        )
                        else "base:v1"
                    )
                    containers = compiled.run.get_all_containers()
                    assert containers
                    assert all(c.image == image for c in containers)
                    assert all(c.command == ["sh", "-c"] for c in containers)
                    assert config.run == local_run
                    assert config.component.run.to_dict() == runtime

    def test_kindless_dag_patch_collects_local_node_file_references(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "base.yaml").write_text("run: {kind: dag}\n")
            (root / "job.yaml").write_text(
                "run: {kind: job, container: {image: busybox:1.36}}\n"
            )
            source = root / "pipeline.yaml"
            source.write_text(
                "pathRef: ./base.yaml\n"
                "run:\n"
                "  operations:\n"
                "    - name: train\n"
                "      pathRef: ./job.yaml\n"
                "      run: {container: {image: busybox:1.37}}\n"
            )
            config = read_polyaxonfile(str(source))

            collect_references(config, str(source))

            node = config.run.operations[0]
            assert node.path_ref == "./job.yaml"
            assert node.component.run.container.image == "busybox:1.36"
            compiled = OperationSpecification.compile_operation(config)
            CompiledOperationSpecification.apply_operation_contexts(compiled)
            assert compiled.run.get_effective_op("train").run.container.image == (
                "busybox:1.37"
            )

    @patch.object(ConfigSpec, "read_from_custom_hub")
    def test_dag_hub_patch_waits_for_the_existing_lookup_stage(self, read_hub):
        config = read_polyaxonfile(
            {
                "run": {
                    "kind": "dag",
                    "operations": [
                        {
                            "name": "train",
                            "hubRef": "train:v1",
                            "run": {"container": {"image": "local:v2"}},
                        }
                    ],
                }
            }
        )
        compiled = OperationSpecification.compile_operation(config)
        compiled.run.resolve_operations(ignore_hub_validation=True)
        node = compiled.run.operations[0]
        assert node.component is None
        assert node.run == {"container": {"image": "local:v2"}}
        read_hub.assert_not_called()

        node.set_definition(
            read_polyaxonfile(
                {"run": {"kind": "job", "container": {"image": "base:v1"}}}
            )
        )
        compiled.run.resolve_operations()

        assert compiled.run.get_effective_op("train").run.container.image == "local:v2"

    def test_dag_templates_and_nested_nodes_collect_relative_references(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            jobs = root / "templates" / "jobs"
            jobs.mkdir(parents=True)
            (jobs / "job.yaml").write_text(
                "kind: operation\n"
                "params: {count: 3}\n"
                "run: {kind: job, container: {image: busybox:1.36}}\n"
            )
            (root / "templates" / "nested.yaml").write_text(
                "kind: component\n"
                "run:\n"
                "  kind: dag\n"
                "  operations:\n"
                "    - name: inner\n"
                "      component: {pathRef: ./jobs/job.yaml}\n"
            )
            source = root / "pipeline.yaml"
            source.write_text(
                "run:\n"
                "  kind: dag\n"
                "  components:\n"
                "    - name: template\n"
                "      pathRef: ./templates/nested.yaml\n"
                "  operations:\n"
                "    - name: from-template\n"
                "      dagRef: template\n"
                "    - name: from-file\n"
                "      pathRef: ./templates/nested.yaml\n"
                "    - name: direct\n"
                "      run:\n"
                "        kind: dag\n"
                "        operations:\n"
                "          - name: inner\n"
                "            pathRef: ./templates/jobs/job.yaml\n"
            )
            config = collect_references(read_polyaxonfile(str(source)), str(source))

            template = config.run.components[0].component
            referenced = config.run.operations[1].component
            for nested in (template, referenced):
                inner = nested.run.operations[0].component
                assert inner.path_ref == "./jobs/job.yaml"
                assert inner.component.kind == "operation"
                assert inner.component.params["count"].value == 3
                assert inner.component.run.container.image == "busybox:1.36"
            direct = config.run.operations[2].run.operations[0]
            assert direct.component.run.container.image == "busybox:1.36"
            assert config.run.operations[0].component is None
            assert template is not referenced
            with patch.object(ConfigSpec, "read_from_file") as read_file:
                collect_references(config, str(source))
            read_file.assert_not_called()

        assert read_polyaxonfile(config.to_json()).to_dict() == config.to_dict()

    def test_dag_source_cycles_and_missing_files_include_the_entry_name(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "pipeline.yaml"
            for field in ("components", "operations"):
                for path, error in (
                    ("./pipeline.yaml", "reference cycle"),
                    ("./missing.yaml", "does not exist"),
                ):
                    with self.subTest(field=field, path=path):
                        source.write_text(
                            "run:\n"
                            "  kind: dag\n"
                            f"  {field}:\n"
                            "    - name: train\n"
                            f"      component: {{pathRef: {path}}}\n"
                        )
                        with self.assertRaisesRegex(
                            PolyaxonSchemaError, f"train.*{error}"
                        ):
                            collect_references(
                                read_polyaxonfile(str(source)), str(source)
                            )

    @patch.object(ConfigSpec, "get_public_registry", return_value=None)
    @patch.object(ConfigSpec, "read_from_custom_hub")
    @patch.object(ConfigSpec, "read_from_url")
    def test_dag_templates_collect_remote_sources(self, read_url, read_hub, registry):
        read_url.return_value = {
            "run": {
                "kind": "dag",
                "operations": [{"name": "train", "hubRef": "org/train:v1"}],
            }
        }
        read_hub.return_value = {
            "kind": "operation",
            "run": {"kind": "job", "container": {"image": "busybox:1.36"}},
        }
        config = read_polyaxonfile(
            {
                "run": {
                    "kind": "dag",
                    "components": [
                        {"name": "template", "urlRef": "https://example.com/dag.yaml"}
                    ],
                    "operations": [{"name": "nested", "dagRef": "template"}],
                }
            }
        )

        collect_references(config)

        train = config.run.components[0].component.run.operations[0]
        assert train.component.kind == "operation"
        assert train.component.run.container.image == "busybox:1.36"
        read_url.assert_called_once_with("https://example.com/dag.yaml")
        read_hub.assert_called_once_with("org/train:v1")
        assert read_polyaxonfile(config.to_json()).to_dict() == config.to_dict()

    def test_dag_expressions_survive_collection_and_serialization(self):
        for run in (
            {"kind": "dag", "operations": "{{ operations }}"},
            {"kind": "dag", "components": "{{ components }}"},
            {
                "kind": "dag",
                "operations": "{{ operations }}",
                "components": "{{ components }}",
                "environment": "{{ environment }}",
            },
            {
                "kind": "dag",
                "operations": [{"name": "train", "dagRef": "template"}],
                "components": "{{ components }}",
            },
        ):
            with self.subTest(run=run):
                config = read_polyaxonfile({"run": run})
                collect_references(config)
                assert config.run.to_dict() == run
                assert config.to_dict() == {"run": run}
                assert read_polyaxonfile(config.to_json()).to_dict() == {"run": run}

    def test_relative_sources_keep_each_files_directory_and_authored_layers(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            jobs = root / "templates" / "jobs"
            jobs.mkdir(parents=True)
            (jobs / "base.yaml").write_text(
                "kind: component\n"
                "inputs: [{name: count, type: int}]\n"
                "params: {count: 1}\n"
                "run:\n"
                "  kind: job\n"
                "  container: {image: base:v1}\n"
            )
            (root / "templates" / "wrapper.yaml").write_text(
                "kind: operation\npathRef: ./jobs/base.yaml\nparams: {count: 2}\n"
                "run: {environment: {annotations: {source: wrapper}}}\n"
            )
            source = root / "run.yaml"
            source.write_text(
                "pathRef: ./templates/wrapper.yaml\n"
                "params: {count: 3}\n"
                "queue: null\n"
                "run:\n"
                "  container: {image: local:v2}\n"
                "runPatch: {container: {image: final:v3}}\n"
                "patchStrategy: pre_merge\n"
            )

            config = read_polyaxonfile(str(source))
            result = collect_references(config, str(source))

            assert result is config
            assert config.path_ref == "./templates/wrapper.yaml"
            assert config.params["count"].value == 3
            assert config.run == {"container": {"image": "local:v2"}}
            assert config.run_patch == {"container": {"image": "final:v3"}}
            assert config.patch_strategy == "pre_merge"
            assert config.queue is None
            assert "queue" in config.model_fields_set
            wrapper = config.component
            assert isinstance(wrapper, V1Polyaxonfile)
            assert wrapper.kind == "operation"
            assert wrapper.path_ref == "./jobs/base.yaml"
            assert wrapper.params["count"].value == 2
            assert wrapper.run == {
                "environment": {"annotations": {"source": "wrapper"}}
            }
            base = wrapper.component
            assert base.kind == "component"
            assert base.inputs[0].name == "count"
            assert base.params["count"].value == 1
            assert base.run.container.image == "base:v1"

            with patch.object(ConfigSpec, "read_from_file") as read_file:
                collect_references(config, str(source))
            read_file.assert_not_called()

        stored = read_polyaxonfile(config.to_json())
        assert stored.to_dict() == config.to_dict()
        assert stored.component.component.run.container.image == "base:v1"

    @patch.object(ConfigSpec, "read_from_url")
    def test_collect_url_chain_without_composing_params(self, read_url):
        wrapper_url = "https://example.com/wrapper.yaml"
        base_url = "https://example.com/base.yaml"
        documents = {
            wrapper_url: {
                "kind": "operation",
                "urlRef": base_url,
                "params": {"count": 2},
                "run": {"container": {"image": "wrapper:v2"}},
            },
            base_url: {
                "params": {"count": 1},
                "run": {
                    "kind": "service",
                    "ports": [8080],
                    "container": {"image": "base:v1"},
                },
            },
        }
        read_url.side_effect = documents.__getitem__
        config = read_polyaxonfile(
            {
                "urlRef": wrapper_url,
                "params": {"count": 3},
                "run": {"container": {"image": "local:v3"}},
            }
        )
        read_url.assert_not_called()

        collect_references(config)

        assert read_url.call_args_list == [call(wrapper_url), call(base_url)]
        assert config.url_ref == wrapper_url
        assert config.params["count"].value == 3
        assert config.component.url_ref == base_url
        assert config.component.params["count"].value == 2
        assert config.component.component.params["count"].value == 1
        assert "component" not in documents[wrapper_url]
        compiled = OperationSpecification.compile_operation(config)
        assert compiled.run.kind == "service"
        assert compiled.run.ports == [8080]
        assert compiled.run.container.image == "local:v3"

    @patch.object(ConfigSpec, "get_public_registry", return_value=None)
    @patch.object(ConfigSpec, "read_from_custom_hub")
    def test_hub_is_loaded_only_when_collection_is_requested(self, read_hub, registry):
        read_hub.return_value = {
            "params": {"count": 1},
            "run": {"kind": "job", "container": {"image": "hub:v1"}},
        }
        config = read_polyaxonfile(
            {
                "hubRef": "train:v1",
                "params": {"count": 3},
                "run": {"container": {"image": "local:v2"}},
            }
        )
        read_hub.assert_not_called()

        collect_references(config)
        collect_references(config)

        read_hub.assert_called_once_with("train:v1")
        assert config.hub_ref == "train:v1"
        assert config.params["count"].value == 3
        assert config.component.params["count"].value == 1
        assert config.component.run.container.image == "hub:v1"
        compiled = OperationSpecification.compile_operation(config)
        assert compiled.run.kind == "job"
        assert compiled.run.container.image == "local:v2"

    def test_stored_reference_and_component_do_not_reload_the_source(self):
        for field, ref in (
            ("pathRef", "/missing/train.yaml"),
            ("urlRef", "https://example.com/train.yaml"),
            ("hubRef", "train:v1"),
            ("dagRef", "train"),
        ):
            config = read_polyaxonfile(
                {
                    field: ref,
                    "component": {
                        "run": {"kind": "job", "container": {"image": "saved:v1"}},
                    },
                }
            )
            with self.subTest(field=field), patch.object(ConfigSpec, "read") as read:
                collect_references(config)

            read.assert_not_called()
            assert config.component.run.container.image == "saved:v1"
            assert config.to_dict()[field] == ref

    def test_collect_legacy_dag_references_in_embedded_component_and_outer_run(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "job.yaml").write_text(
                "kind: component\nrun: {kind: job, container: {image: busybox:1.36}}\n"
            )
            dag = {
                "run": {
                    "kind": "dag",
                    "operations": [{"name": "job", "pathRef": "./job.yaml"}],
                }
            }
            config = read_polyaxonfile({"component": dag, **dag})

            collect_references(config, str(root / "root.yaml"))

        for run in (config.run, config.component.run):
            assert run.operations[0].component.run.container.image == "busybox:1.36"

    def test_missing_path_reports_the_resolved_path(self):
        with TemporaryDirectory() as directory:
            config = read_polyaxonfile(
                {
                    "pathRef": "missing.yaml",
                    "run": {"container": {"image": "local:v2"}},
                }
            )
            with self.assertRaises(PolyaxonfileError) as error:
                collect_references(config, str(Path(directory) / "root.yaml"))

        assert str(Path(directory) / "missing.yaml") in str(error.exception)
        assert "does not exist or is not a file" in str(error.exception)

    def test_invalid_source_reports_its_reference(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.yaml"
            for content in ("", "[]", "kind: compiled_operation", "unknown: true"):
                source.write_text(content)
                config = read_polyaxonfile({"pathRef": str(source)})
                with (
                    self.subTest(content=content),
                    self.assertRaisesRegex(
                        PolyaxonfileError, "Could not resolve pathRef"
                    ),
                ):
                    collect_references(config)

    def test_remote_load_errors_include_the_reference(self):
        for field, ref in (
            ("urlRef", "https://example.com/missing.yaml"),
            ("hubRef", "missing:v1"),
        ):
            config = read_polyaxonfile({field: ref})
            with (
                self.subTest(field=field),
                patch.object(
                    ConfigSpec, "read", side_effect=PolyaxonSchemaError("not found")
                ),
                self.assertRaises(PolyaxonfileError) as error,
            ):
                collect_references(config)

            assert "Could not resolve {} `{}`".format(field, ref) in str(
                error.exception
            )
            assert "not found" in str(error.exception)

    def test_file_cycles_report_the_source_chain(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "nested"
            nested.mkdir()
            source = root / "root.yaml"
            second = nested / "second.yaml"
            second.write_text("pathRef: ../root.yaml\n")

            for ref in ("./root.yaml", "./nested/second.yaml"):
                source.write_text(
                    f"pathRef: {ref}\nrun: {{container: {{image: local:v2}}}}\n"
                )
                config = read_polyaxonfile(str(source))
                with (
                    self.subTest(ref=ref),
                    self.assertRaisesRegex(
                        PolyaxonfileError, "reference cycle"
                    ) as error,
                ):
                    collect_references(config, str(source))
                assert str(source) in str(error.exception)
                if "second" in ref:
                    assert str(second) in str(error.exception)

    @patch.object(ConfigSpec, "read_from_url")
    def test_url_cycle_is_reported_before_fetching_the_same_source_again(
        self, read_url
    ):
        url = "https://example.com/cycle.yaml"
        read_url.return_value = {"urlRef": url}
        config = read_polyaxonfile({"urlRef": url})

        with self.assertRaisesRegex(PolyaxonfileError, "reference cycle"):
            collect_references(config)

        read_url.assert_called_once_with(url)

    @patch.object(ConfigSpec, "get_public_registry", return_value=None)
    @patch.object(ConfigSpec, "read_from_custom_hub")
    def test_hub_cycle_is_reported_before_fetching_the_same_source_again(
        self, read_hub, registry
    ):
        read_hub.return_value = {"hubRef": "train:v1"}
        config = read_polyaxonfile({"hubRef": "train:v1"})

        with self.assertRaisesRegex(PolyaxonfileError, "reference cycle"):
            collect_references(config)

        read_hub.assert_called_once_with("train:v1")

    def test_partial_layers_do_not_require_a_runtime_during_collection(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "params.yaml"
            source.write_text("params: {count: 1}\n")
            config = read_polyaxonfile(
                {"pathRef": str(source), "params": {"count": 3}}, is_preset=True
            )

            collect_references(config)

        assert config.is_preset is True
        assert config.params["count"].value == 3
        assert config.component.params["count"].value == 1
        assert config.run is None
        assert config.component.run is None
        for source in (
            {},
            {"run": {"kind": "dag"}},
        ):
            with self.subTest(source=source):
                config = read_polyaxonfile(source)
                collect_references(config)
                assert config.to_dict() == source

    def test_collection_preserves_unresolved_dag_operations(self):
        config = read_polyaxonfile(
            {"run": {"kind": "dag", "operations": "{{ operations }}"}}
        )

        result = collect_references(config)

        assert result is config
        assert config.run.kind == "dag"
        assert config.run.operations == "{{ operations }}"
