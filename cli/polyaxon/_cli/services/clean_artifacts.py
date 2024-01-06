from typing import List, Union

import click

from clipped.formatting import Printer
from clipped.utils.lists import to_list

from polyaxon._connections import V1ConnectionKind


@click.group()
def clean_artifacts():
    pass


def _delete(
    subpath: Union[str, List[str]],
    connection_name: str,
    connection_kind: str,
    is_file: bool,
):
    from polyaxon._fs.fs import get_fs_from_name
    from polyaxon._fs.manager import delete_file_or_dir

    subpath = to_list(subpath, check_none=True)
    fs = get_fs_from_name(connection_name=connection_name)
    for sp in subpath:
        delete_file_or_dir(
            fs=fs,
            subpath=sp,
            is_file=is_file,
        )
    Printer.success(
        "{} subpath was cleaned, subpath: `{}`".format(connection_kind, subpath)
    )


@clean_artifacts.command()
@click.option("--connection-name", help="The connection name.")
@click.option("-sp", "--subpath", multiple=True, help="The s3 subpath to clean.")
@click.option(
    "--is-file",
    is_flag=True,
    default=False,
    help="whether or not to use the basename of the key.",
)
def s3(connection_name, subpath, is_file):
    """Delete an s3 subpath."""
    _delete(
        subpath=subpath,
        connection_name=connection_name,
        connection_kind=V1ConnectionKind.S3,
        is_file=is_file,
    )


@clean_artifacts.command()
@click.option("--connection-name", help="The connection name.")
@click.option("-sp", "--subpath", multiple=True, help="The gcs subpath to clean.")
@click.option(
    "--is-file",
    is_flag=True,
    default=False,
    help="whether or not to use the basename of the key.",
)
def gcs(connection_name, subpath, is_file):
    """Delete a gcs subpath."""
    _delete(
        subpath=subpath,
        connection_name=connection_name,
        connection_kind=V1ConnectionKind.GCS,
        is_file=is_file,
    )


@clean_artifacts.command()
@click.option("--connection-name", help="The connection name.")
@click.option("-sp", "--subpath", multiple=True, help="The wasb subpath to clean.")
@click.option(
    "--is-file",
    is_flag=True,
    default=False,
    help="whether or not to use the basename of the key.",
)
def wasb(connection_name, subpath, is_file):
    """Delete a wasb path context."""
    _delete(
        subpath=subpath,
        connection_name=connection_name,
        connection_kind=V1ConnectionKind.WASB,
        is_file=is_file,
    )


@clean_artifacts.command()
@click.option("--connection-name", help="The connection name.")
@click.option("-sp", "--subpath", multiple=True, help="The volume subpath to clean.")
@click.option(
    "--is-file",
    is_flag=True,
    default=False,
    help="whether or not to use the basename of the key.",
)
def volume_claim(connection_name, subpath, is_file):
    """Delete a volume path context."""
    _delete(
        subpath=subpath,
        connection_name=connection_name,
        connection_kind=V1ConnectionKind.VOLUME_CLAIM,
        is_file=is_file,
    )


@clean_artifacts.command()
@click.option("--connection-name", help="The connection name.")
@click.option("-sp", "--subpath", multiple=True, help="The host subpath to clean.")
@click.option(
    "--is-file",
    is_flag=True,
    default=False,
    help="whether or not to use the basename of the key.",
)
def host_path(connection_name, subpath, is_file):
    """Delete a host path context."""
    _delete(
        subpath=subpath,
        connection_name=connection_name,
        connection_kind=V1ConnectionKind.HOST_PATH,
        is_file=is_file,
    )
