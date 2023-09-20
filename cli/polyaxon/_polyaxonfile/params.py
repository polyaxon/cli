from collections.abc import Mapping
from typing import Dict, List, Union

from clipped.formatting import Printer

from polyaxon._polyaxonfile.specs.libs.parser import PolyaxonfileParser
from polyaxon.exceptions import PolyaxonfileError


def parse_params(params: Union[List[str], Dict], is_cli: bool = True):
    if isinstance(params, Mapping):
        return {
            k: {"value": PolyaxonfileParser.parse_expression(v, {})}
            for k, v in params.items()
        }

    parsed_params = {}
    for param in params:
        index = param.find("=")
        if index == -1:
            message = (
                "Invalid format for -P parameter: '%s'. Use -P name=value." % param
            )
            if is_cli:
                Printer.error(message, sys_exit=True)
            else:
                raise PolyaxonfileError(message)
        name = param[:index]
        value = param[index + 1 :]
        if name in parsed_params:
            message = "Repeated parameter: '%s'" % name
            if is_cli:
                Printer.error(message, sys_exit=True)
            else:
                raise PolyaxonfileError(message)
        parsed_params[name] = {"value": value}

    return parsed_params


def parse_hparams(hparams: Union[List[str], Dict], is_cli: bool = True):
    if isinstance(hparams, Mapping):
        return hparams

    parsed_params = {}
    for param in hparams:
        index = param.find("=")
        if index == -1:
            message = "Invalid format for -HP parameter: `{}`. Use -HP name='kind:value'.".format(
                param
            )
            if is_cli:
                Printer.error(message, sys_exit=True)
            else:
                raise PolyaxonfileError(message)
        name = param[:index]
        value = param[index + 1 :]
        if name in parsed_params:
            message = "Repeated parameter: `{}`".format(name)
            if is_cli:
                Printer.error(message, sys_exit=True)
            else:
                raise PolyaxonfileError(message)
        values = value.split(":")
        if len(values) < 2:
            message = (
                "Hyper-parameter: `{}` received an incorrect value format `{}`".format(
                    name, value
                )
            )
            if is_cli:
                Printer.error(message, sys_exit=True)
            else:
                raise PolyaxonfileError(message)
        kind = values[0]
        try:
            from polyaxon._config.spec import ConfigSpec

            value = ConfigSpec.read_from_stream(":".join(values[1:]))
        except Exception as e:
            message = (
                "Hyper-parameter: `{}` with kind `{}` received an incorrect value `{}`. "
                "Parsing error: {}".format(name, kind, value, e)
            )
            if is_cli:
                Printer.error(message, sys_exit=True)
            else:
                raise PolyaxonfileError(message)
        parsed_params[name] = {"kind": kind, "value": value}

    return parsed_params
