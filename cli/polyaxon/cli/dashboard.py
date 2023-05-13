import sys

import click

from clipped.formatting import Printer
from clipped.utils.http import clean_host

from polyaxon import settings
from polyaxon.api import POLYAXON_CLOUD_HOST
from polyaxon.logger import clean_outputs


def get_dashboard_url(
    base: str = "ui", subpath: str = "", use_cloud: bool = False
) -> str:
    host = POLYAXON_CLOUD_HOST if use_cloud else clean_host(settings.CLIENT_CONFIG.host)
    dashboard_url = "{}/{}/".format(host, base)
    if subpath:
        return "{}{}/".format(dashboard_url, subpath.rstrip("/"))
    return dashboard_url


def get_dashboard(dashboard_url: str, url_only: bool, yes: bool):
    if url_only:
        Printer.header("The dashboard is available at: {}".format(dashboard_url))
        sys.exit(0)
    if yes or click.confirm(
        "Dashboard page will now open in your browser. Continue?",
        default=True,
    ):
        click.launch(dashboard_url)


@click.command()
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Automatic yes to prompts. "
    'Assume "yes" as answer to all prompts and run non-interactively.',
)
@click.option(
    "--url", is_flag=True, default=False, help="Print the url of the dashboard."
)
@clean_outputs
def dashboard(yes, url):
    """Open dashboard in browser."""
    get_dashboard(dashboard_url=get_dashboard_url(), url_only=url, yes=yes)
