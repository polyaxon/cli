from collections.abc import Mapping
from enum import Enum
from typing import Any, Dict, List, Union

from clipped.formatting import Printer
from polyaxon._polyaxonfile.specs.libs.parser import PolyaxonfileParser
from polyaxon.exceptions import PolyaxonfileError


def _parse_sdk_value(value: Any) -> Any:
    # Strings are sent as given, like -P values, other values serialize as before
    if isinstance(value, str) and not isinstance(value, Enum):
        return value
    if isinstance(value, list):
        return [_parse_sdk_value(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_parse_sdk_value(v) for v in value)
    if isinstance(value, Mapping):
        return {_parse_sdk_value(k): _parse_sdk_value(v) for k, v in value.items()}
    return PolyaxonfileParser.parse_expression(value, {})


def parse_params(params: Union[List[str], Dict], is_cli: bool = True):
    if isinstance(params, Mapping):
        return {k: {"value": _parse_sdk_value(v)} for k, v in params.items()}

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


def parse_env(env: List[str], is_cli: bool = True) -> Dict[str, str]:
    parsed_env = {}
    for value in env:
        name, separator, env_value = value.partition("=")
        if not separator or not name:
            message = "Invalid format for --env: '%s'. Use --env NAME=value." % value
            if is_cli:
                Printer.error(message, sys_exit=True)
            else:
                raise PolyaxonfileError(message)
        if name in parsed_env:
            message = "Repeated env variable: '%s'" % name
            if is_cli:
                Printer.error(message, sys_exit=True)
            else:
                raise PolyaxonfileError(message)
        parsed_env[name] = env_value

    return parsed_env


def parse_ports(ports: List[str], is_cli: bool = True) -> List[int]:
    parsed_ports = []
    for value in ports:
        for port in value.split(","):
            port = port.strip()
            if not (port.isascii() and port.isdigit()):
                message = f"Invalid port '{port}' in '{value}'; use --ports 80,443."
                if is_cli:
                    Printer.error(message, sys_exit=True)
                else:
                    raise PolyaxonfileError(message)
            parsed_ports.append(int(port))

    return parsed_ports
