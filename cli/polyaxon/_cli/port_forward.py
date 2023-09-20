import sys

import click

from clipped.formatting import Printer

from polyaxon import settings
from polyaxon._cli.errors import handle_cli_error
from polyaxon._deploy.schemas.deployment_types import DeploymentTypes
from polyaxon._managers.auth import AuthConfigManager
from polyaxon._managers.cli import CliConfigManager
from polyaxon._managers.client import ClientConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon.logger import clean_outputs


@click.command()
@click.option(
    "-p", "--port", type=int, help="The port to expose the gateway, default to 8000"
)
@click.option(
    "-n",
    "--namespace",
    type=str,
    help="The namespace used for deploying Polyaxon, default polyaxon.",
)
@click.option(
    "-t",
    "--deployment-type",
    help="Deployment type.",
)
@click.option(
    "-r",
    "--release-name",
    type=str,
    help="The release name used for deploying Polyaxon, default polyaxon.",
)
@click.option(
    "-s", "--service", type=str, help="The service to forward, default 'gateway'."
)
@click.option("-add", "--address", type=str, help="The host address.")
@clean_outputs
def port_forward(port, namespace, deployment_type, release_name, service, address):
    """If you deploy Polyaxon using ClusterIP, you can use this command
    to access the gateway through `localhost:port`.
    """
    from polyaxon._deploy.operators.kubectl import KubectlOperator

    if not port and deployment_type in [
        DeploymentTypes.MICRO_K8S,
        DeploymentTypes.MINIKUBE,
    ]:
        port = 31833
    port = port or 8000
    namespace = namespace or "polyaxon"
    release_name = release_name or "polyaxon"
    service = service or "gateway"

    kubectl = KubectlOperator()
    args = [
        "port-forward",
        "-n",
        namespace,
        "svc/{}-polyaxon-{}".format(release_name, service),
        "{}:80".format(port),
    ]
    if address:
        args.extend(["--address", address])
    else:
        address = "localhost"

    try:
        _config = ClientConfigManager.get_config_or_default()
    except Exception as e:
        handle_cli_error(e, message="Polyaxon load configuration.")
        Printer.heading("You can reset your config by running: `polyaxon config purge`")
        sys.exit(1)

    _config.host = "http://{}:{}".format(address, port)
    ClientConfigManager.set_config(_config)
    CliConfigManager.purge()
    AuthConfigManager.purge()
    UserConfigManager.purge()
    Printer.header("Client configuration is updated!")
    Printer.success("Polyaxon will be available at: {}".format(_config.host))
    stdout = kubectl.execute(
        args=args, is_json=False, stream=settings.CLIENT_CONFIG.debug
    )
    Printer.print(stdout)
