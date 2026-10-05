from collections.abc import Mapping
import os
from typing import Optional, Union

from polyaxon._config.spec import ConfigSpec
from polyaxon._flow.operations.operation import V1Operation
from polyaxon._flow.polyaxonfile import V1Polyaxonfile
from polyaxon._flow.run.dag import V1Dag
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.patch import validate_run_patch
from polyaxon._polyaxonfile.specs import read_polyaxonfile
from polyaxon.exceptions import PolyaxonfileError, PolyaxonSchemaError


def collect_dag_components(
    dag: Union[V1Dag, Mapping], path_context: Optional[str] = None, sources=()
):
    """Collect references in typed DAGs and partial runtime overlays."""
    if path_context and not sources:
        sources = (("pathRef", os.path.realpath(path_context)),)
    for field in ("components", "operations"):
        entries = dag.get(field) if isinstance(dag, Mapping) else getattr(dag, field)
        if not isinstance(entries, list):
            continue
        for index, op in enumerate(entries):
            if isinstance(op, Mapping):
                op = read_polyaxonfile(op)
                entries[index] = op
            elif not isinstance(op, V1Polyaxonfile):
                # Leave malformed entries to runtime validation.
                continue
            try:
                _collect_shared_references(op, path_context, sources)
            except Exception as e:
                raise PolyaxonSchemaError(
                    "Pipeline op with name `{}` requires a component with ref `{}`, "
                    "the reference could not be resolved. Error: {}".format(
                        op.name, op.hub_ref or op.url_ref or op.path_ref, e
                    )
                ) from e


def collect_references(
    config: Union[V1Operation, V1Polyaxonfile], path_context: Optional[str] = None
):
    sources = (("pathRef", os.path.realpath(path_context)),) if path_context else ()
    return _collect_shared_references(config, path_context, sources)


def _collect_shared_references(config, path_context, sources):
    if config.component is not None:
        _collect_shared_references(config.component, path_context, sources)
    else:
        reference = None
        source_path = path_context
        if config.hub_ref:
            reference = ("hubRef", config.hub_ref)
            source = ConfigSpec.get_from(config.hub_ref, "hub")
        elif config.url_ref:
            reference = ("urlRef", config.url_ref)
            source = ConfigSpec.get_from(config.url_ref, "url")
        elif config.path_ref:
            source_path = config.path_ref
            if path_context:
                source_path = os.path.join(
                    os.path.dirname(os.path.abspath(path_context)), source_path
                )
            source_path = os.path.abspath(source_path)
            reference = ("pathRef", os.path.realpath(source_path))
            if not os.path.isfile(source_path):
                raise PolyaxonfileError(
                    "Path ref `{}` does not exist or is not a file.".format(source_path)
                )
            source = ConfigSpec.get_from(source_path)

        if reference:
            if reference in sources:
                chain = " -> ".join(
                    "{} `{}`".format(*ref) for ref in (*sources, reference)
                )
                raise PolyaxonfileError(
                    "Polyaxonfile reference cycle: {}".format(chain)
                )
            try:
                component = read_polyaxonfile(source)
                _collect_shared_references(
                    component, source_path, (*sources, reference)
                )
            except Exception as e:
                raise PolyaxonfileError(
                    "Could not resolve {} `{}`: {}".format(*reference, e)
                ) from e
            config.component = component

    if isinstance(config.run, Mapping) and config.component is not None:
        native_run = config.component.get_native_run()
        if native_run is not None and native_run.kind == V1RunKind.DAG:
            # Parse local DAG entries so their file references can be collected.
            config.run = validate_run_patch(config.run, native_run.kind)

    if config.is_dag_run:
        collect_dag_components(config.run, path_context, sources)
    return config
