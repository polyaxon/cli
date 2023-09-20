import sys

import click

from clipped.compact.pydantic import ValidationError
from clipped.formatting import Printer
from clipped.types.docker_image import validate_image
from clipped.utils.paths import copy_file

from polyaxon._cli.check import check_polyaxonfile
from polyaxon._cli.errors import handle_cli_error
from polyaxon._config.spec import ConfigSpec
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
)
from polyaxon._schemas.types import V1DockerfileType
from polyaxon.exceptions import PolyaxonBuildException, PolyaxonSchemaError


@click.group()
def docker():
    pass


@docker.command()
@click.option(
    "-f",
    "--file",
    "polyaxonfile",
    multiple=True,
    type=click.Path(exists=True),
    help="The polyaxonfiles to generate the dockerfile from.",
)
@click.option(
    "-pm",
    "--python-module",
    type=str,
    help="The python module to run.",
)
@click.option(
    "--build-context",
    help="The build context config to generate the dockerfile from.",
)
@click.option(
    "-dest", "--destination", help="The destination where to generate the build."
)
@click.option("--copy-path", help="Copy generated files to a specific path.")
@click.option(
    "--params",
    "--param",
    "-P",
    metavar="NAME=VALUE",
    multiple=True,
    help="A parameter to override the default params of the run, form -P name=value.",
)
@click.option(
    "--track",
    is_flag=True,
    default=False,
    help="Flag to track or not the file content.",
)
def generate(
    polyaxonfile, python_module, build_context, destination, copy_path, params, track
):
    """Generate a dockerfile given the polyaxonfile."""
    from clipped.utils.hashing import hash_value

    from polyaxon._docker.builder import DockerFileGenerator
    from polyaxon._init.dockerfile import create_dockerfile_lineage

    if all([polyaxonfile, build_context]):
        Printer.error("Only a polyaxonfile or a build context option is required.")
        sys.exit(1)

    if build_context:
        try:
            build_context = [
                V1DockerfileType.from_dict(ConfigSpec.read_from(build_context))
            ]
        except (PolyaxonSchemaError, ValidationError) as e:
            Printer.error("received a non valid build context.")
            Printer.error("Error message: {}.".format(e))
            sys.exit(1)
    else:
        specification = check_polyaxonfile(
            polyaxonfile=polyaxonfile,
            python_module=python_module,
            params=params,
            verbose=False,
        )

        try:
            compiled_operation = OperationSpecification.compile_operation(specification)
            compiled_operation.apply_params(params=specification.config.params)
            compiled_operation = (
                CompiledOperationSpecification.apply_operation_contexts(
                    compiled_operation
                )
            )
        except (PolyaxonSchemaError, ValidationError):
            Printer.error(
                "Could not run this polyaxonfile locally, "
                "a context is required to resolve it dependencies."
            )
            sys.exit(1)

        build_context = compiled_operation.init_dockerfiles

    for init_dockerfile in build_context:
        generator = DockerFileGenerator(
            build_context=init_dockerfile, destination=destination or "."
        )
        generator.create()
        Printer.success(
            "Dockerfile was generated, path: `{}`".format(generator.dockerfile_path)
        )

        dockerfile_path = generator.dockerfile_path
        if copy_path:
            dockerfile_path = copy_file(dockerfile_path, copy_path)
        if track:
            hash_content = hash_value(init_dockerfile.to_dict())
            create_dockerfile_lineage(dockerfile_path, summary={"hash": hash_content})


@docker.command()
@click.option(
    "-c",
    "--context",
    required=True,
    type=click.Path(exists=True),
    help="A build context accessible to Polyaxon.",
)
@click.option(
    "-d", "--destination", help="The tagged image destination $PROJECT/$IMAGE:$TAG."
)
@click.option(
    "--nocache",
    is_flag=True,
    default=False,
    show_default=False,
    help="To force rebuild the image.",
)
@click.option(
    "--max-retries",
    type=int,
    default=3,
    help="Number of times to retry the build process.",
)
@click.option(
    "--sleep-interval",
    type=int,
    default=2,
    help="Sleep interval between retries in seconds.",
)
@click.option(
    "--reraise",
    is_flag=True,
    default=False,
    show_default=False,
    help="To force rebuild the image.",
)
def build(context, destination, nocache, max_retries, sleep_interval, reraise):
    """Build a dockerfile, this command required Docker to be installed."""
    from polyaxon._docker.builder import build

    try:
        validate_image(destination)
    except ValueError as e:
        handle_cli_error(e, message="Image destination is invalid.")

    try:
        build(
            context=context,
            destination=destination,
            nocache=nocache,
            max_retries=max_retries,
            sleep_interval=sleep_interval,
        )
    except PolyaxonBuildException as e:
        handle_cli_error(e, message="Docker build failed")
        if reraise:
            raise e
        sys.exit(1)


@docker.command()
@click.option(
    "-d", "--destination", help="The tagged image destination $PROJECT/$IMAGE:$TAG."
)
@click.option(
    "--max-retries",
    "--max-retries",
    type=int,
    default=3,
    help="Number of times to retry the build process.",
)
@click.option(
    "--sleep-interval",
    type=int,
    default=2,
    help="Sleep interval between retries in seconds.",
)
@click.option(
    "--reraise",
    is_flag=True,
    default=False,
    show_default=False,
    help="To force rebuild the image.",
)
def push(destination, max_retries, sleep_interval, reraise):
    """Push an image, this command required Docker to be installed."""
    from polyaxon._docker.builder import push

    try:
        push(
            destination=destination,
            max_retries=max_retries,
            sleep_interval=sleep_interval,
        )
    except PolyaxonBuildException as e:
        handle_cli_error(e, message="Docker push failed")
        if reraise:
            raise e
        sys.exit(1)


@docker.command()
@click.option(
    "-c",
    "--context",
    required=True,
    type=click.Path(exists=True),
    help="A build context accessible to Polyaxon.",
)
@click.option(
    "-d", "--destination", help="The tagged image destination $PROJECT/$IMAGE:$TAG."
)
@click.option(
    "--nocache",
    is_flag=True,
    default=False,
    show_default=False,
    help="To force rebuild the image.",
)
@click.option(
    "--max_retries",
    "--max-retries",
    type=int,
    default=3,
    help="Number of times to retry the build process.",
)
@click.option(
    "--sleep-interval",
    type=int,
    default=2,
    help="Sleep interval between retries in seconds.",
)
@click.option(
    "--reraise",
    is_flag=True,
    default=False,
    show_default=False,
    help="To force rebuild the image.",
)
def build_and_push(context, destination, nocache, max_retries, sleep_interval, reraise):
    """
    Build a dockerfile and push it to the provided registry,
    this command required Docker to be installed.
    """

    from polyaxon._docker.builder import build_and_push

    try:
        build_and_push(
            context=context,
            destination=destination,
            nocache=nocache,
            max_retries=max_retries,
            sleep_interval=sleep_interval,
        )
    except PolyaxonBuildException as e:
        handle_cli_error(e, message="Docker build and push failed")
        if reraise:
            raise e
        sys.exit(1)
