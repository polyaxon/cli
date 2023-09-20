import click

from clipped.formatting import Printer

from polyaxon._polyaxonfile.check import check_polyaxonfile
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
    "--lint",
    "-l",
    is_flag=True,
    default=False,
    help="To check the specification only without params validation.",
)
@clean_outputs
def check(polyaxonfile, python_module, version, params, lint):
    """Check a polyaxonfile."""
    specification = check_polyaxonfile(
        polyaxonfile=polyaxonfile,
        python_module=python_module,
        params=params,
        validate_params=not lint,
    )

    if version:
        Printer.decorate_format_value(
            "The version is: {}", specification.version, "yellow"
        )
    return specification
