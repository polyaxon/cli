import os
import time

import click

from clipped.formatting import Printer
from clipped.utils.lists import to_list
from clipped.utils.validation import validate_tags

from polyaxon._cli.dashboard import get_dashboard, get_dashboard_url
from polyaxon._cli.errors import handle_cli_error
from polyaxon._managers.deploy import DeployConfigManager
from polyaxon._utils.fqn_utils import get_resource_name
from polyaxon.logger import clean_outputs


def read_deployment_config(filepaths, command: str):
    from polyaxon._deploy import reader

    if not filepaths:
        return None

    filepaths = to_list(filepaths)
    for filepath in filepaths:
        if not os.path.isfile(filepath):
            Printer.error(
                "`{}` must be a valid file".format(filepath),
                sys_exit=True,
                command_help="polyaxon admin {}".format(command),
            )
    try:
        deployment_config = reader.read(filepaths)
        return deployment_config
    except Exception as e:
        handle_cli_error(
            e, message="Polyaxon deployment file is not valid", sys_exit=True
        )


@click.group()
@clean_outputs
def admin():
    """Commands for admin management."""


@admin.command()
@click.option(
    "-f",
    "--file",
    "config_file",
    type=click.Path(exists=True),
    help="The polyaxon deployment config file(s) to check.",
)
@click.option(
    "-t",
    "--deployment-type",
    help="Deployment type.",
)
@click.option(
    "--manager-path",
    type=click.Path(exists=True),
    help="The path of the deployment manager, e.g. local chart.",
)
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Check if deployment file and other requirements are met.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Dry run the configuration and generate a debuggable output.",
)
@clean_outputs
def deploy(config_file, deployment_type, manager_path, check, dry_run):
    """Deploy polyaxon."""
    config = read_deployment_config(config_file, command="deploy")
    manager = DeployConfigManager(
        config=config,
        filepath=config_file,
        deployment_type=deployment_type,
        manager_path=manager_path,
        dry_run=dry_run,
    )
    exception = None
    if config:
        Printer.success(
            "Polyaxon `{}` deployment file is valid".format(config.deployment_chart)
        )
    if check:
        try:
            manager.check()
        except Exception as e:
            handle_cli_error(
                e, message="Polyaxon deployment manager error", sys_exit=True
            )

    else:
        try:
            manager.install()
        except Exception as e:
            Printer.error("Polyaxon could not be installed")
            exception = e

    if exception:
        Printer.error("Error message: {}".format(exception), sys_exit=True)


@admin.command()
@click.option(
    "-f",
    "--file",
    "config_file",
    type=click.Path(exists=True),
    help="The polyaxon deployment config file(s) to check.",
)
@click.option(
    "-t",
    "--deployment-type",
    help="Deployment type.",
)
@click.option(
    "--manager-path",
    type=click.Path(exists=True),
    help="The path of the deployment manager, e.g. local chart.",
)
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Check if deployment file and other requirements are met.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Dry run the configuration and generate a debuggable output.",
)
@clean_outputs
def upgrade(config_file, deployment_type, manager_path, check, dry_run):
    """Upgrade a Polyaxon deployment."""
    config = read_deployment_config(config_file, command="upgrade")
    manager = DeployConfigManager(
        config=config,
        filepath=config_file,
        deployment_type=deployment_type,
        manager_path=manager_path,
        dry_run=dry_run,
    )
    exception = None
    if config:
        Printer.success(
            "Polyaxon `{}` deployment file is valid".format(config.deployment_chart)
        )
    if check:
        try:
            manager.check()
        except Exception as e:
            handle_cli_error(
                e, message="Polyaxon deployment manager error", sys_exit=True
            )
    else:
        try:
            manager.upgrade()
        except Exception as e:
            Printer.error("Polyaxon could not upgrade the deployment")
            exception = e

    if exception:
        Printer.error("Error message: {}".format(exception))


@admin.command()
@click.option(
    "-f",
    "--file",
    "config_file",
    type=click.Path(exists=True),
    help="The polyaxon deployment config file(s) to check.",
)
@click.option(
    "--manager-path",
    type=click.Path(exists=True),
    help="The path of the deployment manager, e.g. local chart.",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Automatic yes to prompts. "
    'Assume "yes" as answer to all prompts and run non-interactively.',
)
@clean_outputs
def teardown(config_file, manager_path, yes):
    """Teardown a polyaxon deployment given a config file."""
    config = read_deployment_config(config_file, command="teardown")
    manager = DeployConfigManager(
        config=config, filepath=config_file, manager_path=manager_path
    )
    exception = None
    try:
        if yes or click.confirm(
            "Would you like to execute pre-delete hooks?", default=False
        ):
            manager.teardown(hooks=True)
        else:
            manager.teardown(hooks=False)
    except Exception as e:
        Printer.error("Polyaxon could not teardown the deployment")
        exception = e

    if exception:
        Printer.error("Error message: {}".format(exception))


@admin.command()
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
    get_dashboard(dashboard_url=get_dashboard_url(base="_admin"), url_only=url, yes=yes)


@admin.command()
@click.option("--namespace", "-n", type=str)
@click.option("--in-cluster", is_flag=True, default=False)
@click.option("--delete", "-d", is_flag=True, default=False)
@click.option(
    "--uuids",
    "--uids",
    type=str,
    help="List of uuid of operations to clean/delete (comma separated values).",
)
def clean_ops(namespace, in_cluster, delete, uuids):
    """clean-ops command."""
    from polyaxon._k8s.custom_resources import operation
    from polyaxon._k8s.manager.manager import K8sManager

    if not namespace:
        raise Printer.error("The argument `--namespace` is required!", sys_exit=True)

    manager = K8sManager(namespace=namespace, in_cluster=in_cluster)

    def _patch_op():
        retry = 0
        while retry < 3:
            if retry:
                time.sleep(retry * 2)
            try:
                manager.update_custom_object(
                    name=op,
                    group=operation.GROUP,
                    version=operation.API_VERSION,
                    plural=operation.PLURAL,
                    body={"metadata": {"finalizers": None}},
                )
                return
            except Exception as e:
                print("Exception %s", e)
                print("retrying")
                retry += 1

    def _delete_op():
        retry = 0
        while retry <= 2:
            if retry:
                time.sleep(retry)
            try:
                manager.delete_custom_object(
                    name=op,
                    group=operation.GROUP,
                    version=operation.API_VERSION,
                    plural=operation.PLURAL,
                )
                return
            except Exception as e:
                print("Exception %s", e)
                print("retrying")
                retry += 1

    uuids = validate_tags(uuids, validate_yaml=True)
    if uuids:
        ops = [o if "plx-operation-" in o else get_resource_name(o) for o in uuids]
    else:
        ops = [
            o["metadata"]["name"]
            for o in manager.list_custom_objects(
                group=operation.GROUP,
                version=operation.API_VERSION,
                plural=operation.PLURAL,
            )
        ]
    if not ops:
        return

    Printer.header(f"Cleaning {len(ops)} ops ...")
    for idx, op in enumerate(ops):
        with Printer.console.status(f"Cleaning operation {idx + 1}/{len(ops)} ..."):
            _patch_op()
            if delete:
                _delete_op()
        Printer.success(f"Operation {op} was cleaned")
