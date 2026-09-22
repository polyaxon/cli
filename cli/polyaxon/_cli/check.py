import click

from clipped.formatting import Printer
from polyaxon.logger import clean_outputs


@click.command()
@click.option(
    "-f",
    "--file",
    "polyaxonfile",
    multiple=True,
    type=click.Path(exists=True),
    help="The polyaxon file to check.",
)
@click.option(
    "-pm",
    "--python-module",
    type=str,
    help="The python module to run.",
)
@click.option(
    "--version",
    "-v",
    is_flag=True,
    default=False,
    help="Checks and prints the version.",
)
@click.option(
    "--params",
    "--param",
    "-P",
    metavar="NAME=VALUE",
    multiple=True,
    help="A parameter to override the default params of the run, form -P name=value.",
)
@click.option(
    "--strict-params/--no-strict-params",
    default=None,
    help="Set the operation's strict parameter policy. Strict mode requires "
    "undeclared params to set contextOnly: true. Defaults to the specification's "
    "policy; a strict component remains strict.",
)
@click.option(
    "--lint",
    "-l",
    is_flag=True,
    default=False,
    help="To check the specification only without params validation.",
)
@clean_outputs
def check(polyaxonfile, python_module, version, params, strict_params, lint):
    """Check a polyaxonfile."""
    from polyaxon._polyaxonfile.check import check_polyaxonfile

    specification = check_polyaxonfile(
        polyaxonfile=polyaxonfile,
        python_module=python_module,
        params=params,
        strict_params=strict_params,
        validate_params=not lint,
    )

    if version:
        Printer.decorate_format_value(
            "The version is: {}", specification.version, "yellow"
        )
    return specification
