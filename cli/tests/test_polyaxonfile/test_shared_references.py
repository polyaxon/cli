from mock import call, patch
from pathlib import Path
import pytest
from tempfile import TemporaryDirectory

from polyaxon._config.spec import ConfigSpec
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._polyaxonfile import read_polyaxonfile
from polyaxon._polyaxonfile.check import collect_references
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonfileError, PolyaxonSchemaError


@pytest.mark.polyaxonfile_mark
class TestSharedReferences(BaseTestCase):
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
            )
            source = root / "run.yaml"
            source.write_text(
                "pathRef: ./templates/wrapper.yaml\n"
                "params: {count: 3}\n"
                "queue: null\n"
                "run:\n"
                "  kind: job\n"
                "  container: {image: local:v2}\n"
                "runPatch: {container: {image: final:v3}}\n"
                "patchStrategy: pre_merge\n"
            )

            config = read_polyaxonfile(str(source))
            result = collect_references(config, str(source))

            assert result is config
            assert config.path_ref == "./templates/wrapper.yaml"
            assert config.params["count"].value == 3
            assert config.run.container.image == "local:v2"
            assert config.run_patch == {"container": {"image": "final:v3"}}
            assert config.patch_strategy == "pre_merge"
            assert config.queue is None
            assert "queue" in config.model_fields_set
            wrapper = config.component
            assert isinstance(wrapper, V1Polyaxonfile)
            assert wrapper.kind == "operation"
            assert wrapper.path_ref == "./jobs/base.yaml"
            assert wrapper.params["count"].value == 2
            assert wrapper.run is None
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
            },
            base_url: {
                "params": {"count": 1},
                "run": {"kind": "job", "container": {"image": "base:v1"}},
            },
        }
        read_url.side_effect = documents.__getitem__
        config = read_polyaxonfile({"urlRef": wrapper_url, "params": {"count": 3}})
        read_url.assert_not_called()

        collect_references(config)

        assert read_url.call_args_list == [call(wrapper_url), call(base_url)]
        assert config.url_ref == wrapper_url
        assert config.params["count"].value == 3
        assert config.component.url_ref == base_url
        assert config.component.params["count"].value == 2
        assert config.component.component.params["count"].value == 1
        assert "component" not in documents[wrapper_url]

    @patch.object(ConfigSpec, "get_public_registry", return_value=None)
    @patch.object(ConfigSpec, "read_from_custom_hub")
    def test_hub_is_loaded_only_when_collection_is_requested(self, read_hub, registry):
        read_hub.return_value = {
            "params": {"count": 1},
            "run": {"kind": "job", "container": {"image": "hub:v1"}},
        }
        config = read_polyaxonfile({"hubRef": "train:v1", "params": {"count": 3}})
        read_hub.assert_not_called()

        collect_references(config)
        collect_references(config)

        read_hub.assert_called_once_with("train:v1")
        assert config.hub_ref == "train:v1"
        assert config.params["count"].value == 3
        assert config.component.params["count"].value == 1
        assert config.component.run.container.image == "hub:v1"

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
            config = read_polyaxonfile({"pathRef": "missing.yaml"})
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
                source.write_text("pathRef: {}\n".format(ref))
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
