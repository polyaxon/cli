import os

from collections import OrderedDict
from typing import Dict, List, Optional, Union

from clipped.formatting import Printer
from clipped.utils.lists import to_list

from polyaxon._cli.errors import handle_cli_error
from polyaxon._config.spec import ConfigSpec
from polyaxon._flow import V1Dag, V1Init, V1Matrix, V1Operation
from polyaxon._polyaxonfile.manager import get_op_specification
from polyaxon._polyaxonfile.params import parse_hparams, parse_params
from polyaxon._polyaxonfile.specs import get_specification, kinds
from polyaxon.exceptions import PolyaxonfileError, PolyaxonSchemaError


def collect_dag_components(dag: V1Dag, path_context: Optional[str] = None):
    """Collect components that cannot be resolved by the scheduler"""
    for op in dag.operations:
        op_name = op.name
        if op.has_url_reference or op.has_path_reference or op.has_hub_reference:
            try:
                op = collect_references(op, path_context)
            except Exception as e:
                raise PolyaxonSchemaError(
                    "Pipeline op with name `{}` requires a component with ref `{}`, "
                    "the reference could not be resolved. Error: {}".format(
                        op_name, op.hub_ref or op.url_ref or op.path_ref, e
                    )
                )


def collect_references(config: V1Operation, path_context: Optional[str] = None):
    if config.has_component_reference:
        return config
    elif config.has_hub_reference:
        component = ConfigSpec.get_from(config.hub_ref, "hub").read()
    elif config.has_url_reference:
        component = ConfigSpec.get_from(config.url_ref, "url").read()
    elif config.has_path_reference:
        path_ref = config.path_ref
        if path_context:
            path_ref = os.path.join(
                os.path.dirname(os.path.abspath(path_context)), path_ref
            )
        component = ConfigSpec.get_from(path_ref).read()
        path_context = path_ref
    else:
        raise PolyaxonfileError("Operation found without component")
    component = get_specification(data=component)
    if component.kind != kinds.COMPONENT:
        if config.has_url_reference:
            ref_type = "Url ref"
            ref = config.url_ref
        else:
            ref_type = "Path ref"
            ref = config.path_ref
        raise PolyaxonfileError(
            "the reference ({}) `{}` is of kind `{}`, it should be a `{}`".format(
                ref, ref_type, component.kind, kinds.COMPONENT
            )
        )
    config.component = component
    if component.is_dag_run:
        collect_dag_components(component.run, path_context)
    return config


def check_polyaxonfile(
    polyaxonfile: Optional[str] = None,
    python_module: Optional[str] = None,
    url: Optional[str] = None,
    hub: Optional[str] = None,
    params: Optional[Union[List[str], Dict]] = None,
    hparams: Optional[Union[List[str], Dict]] = None,
    matrix_kind: Optional[str] = None,
    matrix_concurrency: Optional[int] = None,
    matrix_num_runs: Optional[int] = None,
    matrix: Optional[Union[Dict, V1Matrix]] = None,
    presets: Optional[List[str]] = None,
    queue: Optional[str] = None,
    namespace: Optional[str] = None,
    nocache: Optional[bool] = None,
    cache: Optional[Union[int, str, bool]] = None,
    verbose: bool = True,
    is_cli: bool = True,
    to_op: bool = True,
    validate_params: bool = True,
    approved: Optional[Union[int, str, bool]] = None,
    git_init: Optional[V1Init] = None,
    ignore_template: bool = False,
):
    if sum([1 for i in [python_module, url, hub] if i]) > 1:
        message = (
            "You can only use one and only one option: "
            "hub, url, or a python module.".format(hub)
        )
        if is_cli:
            Printer.error(message, sys_exit=True)
        else:
            raise PolyaxonfileError(message)
    if not any([polyaxonfile, python_module, url, hub]):
        polyaxonfile = check_default_path(path=".")
    if not any([polyaxonfile, python_module, url, hub]):
        message = (
            "Something went wrong, `check_polyaxonfile` was called without a polyaxonfile, "
            "a hub component reference, a url or a python module."
        )
        if is_cli:
            Printer.error(message, sys_exit=True)
        else:
            raise PolyaxonfileError(message)
    if hub and not to_op:
        message = "Something went wrong, calling hub component `{}` without operation.".format(
            hub
        )
        if is_cli:
            Printer.error(message, sys_exit=True)
        else:
            raise PolyaxonfileError(message)

    polyaxonfile = to_list(polyaxonfile, check_none=True)

    parsed_params = None
    if params:
        parsed_params = parse_params(params, is_cli=is_cli)
    parsed_hparams = None
    if hparams:
        parsed_hparams = parse_hparams(hparams, is_cli=is_cli)

    if not any([os.path.isfile(f) for f in polyaxonfile]) and not any(
        [python_module, url, hub]
    ):
        message = "Please pass a valid polyaxonfile, a python module, a url, or a component name"
        if is_cli:
            Printer.error(message, sys_exit=True)
        else:
            raise PolyaxonfileError(message)

    try:
        path_context = None

        if python_module:
            path_context = python_module
            plx_file = (
                ConfigSpec.get_from(python_module, config_type=".py")
                .read()
                .to_dict(include_kind=True, include_version=True)
            )
        elif url:
            plx_file = ConfigSpec.get_from(url, "url").read()
        elif hub:
            plx_file = ConfigSpec.get_from(hub, "hub").read()
        else:
            path_context = polyaxonfile.pop(0)
            plx_file = ConfigSpec.read_from(path_context)

        plx_file = get_specification(data=plx_file)
        if plx_file.kind == kinds.OPERATION:
            plx_file = collect_references(plx_file, path_context)
            plx_component = plx_file.component
        else:
            plx_component = plx_file

        if plx_component.is_dag_run:
            collect_dag_components(plx_component.run, path_context)

        if to_op or hub:
            plx_file = get_op_specification(
                hub=hub,
                config=plx_file,
                params=parsed_params,
                hparams=parsed_hparams,
                matrix_kind=matrix_kind,
                matrix_concurrency=matrix_concurrency,
                matrix_num_runs=matrix_num_runs,
                matrix=matrix,
                presets=presets,
                queue=queue,
                namespace=namespace,
                nocache=nocache,
                cache=cache,
                approved=approved,
                validate_params=validate_params,
                preset_files=polyaxonfile,
                git_init=git_init,
            )
        if verbose and is_cli:
            Printer.success("Polyaxonfile valid")
        if ignore_template:
            plx_file.disable_template()
        if plx_file.is_template():
            template_message = "This polyaxonfile was marked as template by the owner:"
            if plx_file.template.description:
                template_message += "\ntemplate description: {}".format(
                    plx_file.template.description
                )
            if plx_file.template.fields:
                template_message += "\ntemplate fields that need changes: {}".format(
                    plx_file.template.fields
                )
            Printer.warning(template_message)
        return plx_file
    except Exception as e:
        message = "Polyaxonfile is not valid."
        if is_cli:
            handle_cli_error(e, message=message, sys_exit=True)
        else:
            raise PolyaxonfileError(message) from e


def check_polyaxonfile_kind(specification, kind):
    if specification.kind != kind:
        Printer.error(
            "Your polyaxonfile must be of kind: `{}`, "
            "received: `{}`.".format(kind, specification.kind),
            sys_exit=True,
        )


def get_matrix_info(kind, concurrency, early_stopping=False, **kwargs):
    info = OrderedDict()
    info["Matrix kind"] = kind.lower()
    info["Concurrency"] = (
        "{} runs".format("sequential")
        if concurrency == 1
        else "{} concurrent runs".format(concurrency)
    )
    info["Early stopping"] = "activated" if early_stopping else "deactivated"
    if "num_runs" in kwargs:
        info["Num of runs to create"] = kwargs["num_runs"]

    Printer.dict_tabulate(info)


DEFAULT_POLYAXON_FILE_NAME = [
    "polyaxon",
    "polyaxonci",
    "polyaxon-ci",
    "polyaxon.ci",
    "polyaxonfile",
]

DEFAULT_POLYAXON_FILE_EXTENSION = ["yaml", "yml", "json"]


def check_default_path(path):
    path = os.path.abspath(path)
    for filename in DEFAULT_POLYAXON_FILE_NAME:
        for ext in DEFAULT_POLYAXON_FILE_EXTENSION:
            filepath = os.path.join(path, "{}.{}".format(filename, ext))
            if os.path.isfile(filepath):
                return filepath
