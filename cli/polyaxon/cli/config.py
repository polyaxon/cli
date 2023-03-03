#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

import click

from polyaxon import settings
from polyaxon.cli.errors import handle_cli_error
from polyaxon.cli.session import set_versions_config
from polyaxon.logger import clean_outputs, logger
from polyaxon.managers.cli import CliConfigManager
from polyaxon.managers.client import ClientConfigManager
from polyaxon.managers.home import HomeConfigManager
from polyaxon.managers.user import UserConfigManager
from polyaxon.utils.formatting import Printer, dict_tabulate, dict_to_tabulate


def validate_options(ctx, param, value):
    possible_values = ["verbose", "host"]
    if value and value not in possible_values:
        raise click.BadParameter(
            "Value `{}` is not supported, must one of the value {}".format(
                value, possible_values
            )
        )
    return value


@click.group(invoke_without_command=True)
@click.option(
    "--list",
    "-l",
    "_list",
    is_flag=True,
    help="Deprecated, please use `polyaxon config show`.",
)
@clean_outputs
def config(_list):  # pylint:disable=redefined-builtin
    """Set and get the global configurations."""
    if _list:
        Printer.warning(
            "`polyaxon config -l` is deprecated, please use `polyaxon config show`!"
        )


@config.command()
@clean_outputs
def show():
    """Show the current cli, client, and user configs."""
    _config = HomeConfigManager.get_config_or_default()
    Printer.heading(
        "In addition to environment variables, global configs will be loaded from:"
    )
    dict_tabulate(_config.to_dict())
    _config = ClientConfigManager.get_config_or_default()
    Printer.heading("Client config:")
    dict_tabulate(_config.to_dict())
    _config = CliConfigManager.get_config_or_default()
    if _config:
        Printer.heading("CLI config:")
        if _config.current_version:
            Printer.print("Version {}".format(_config.current_version))
        else:
            Printer.warning("This cli is not configured.")
        if _config.installation:
            config_installation = dict_to_tabulate(
                _config.installation,
                humanize_values=True,
                exclude_attrs=["hmac", "auth", "host"],
            )
            Printer.heading("Platform config:")
            dict_tabulate(config_installation)
        else:
            Printer.warning("This cli is not connected to a Polyaxon Host.")
    _config = UserConfigManager.get_config_or_default()
    if _config:
        Printer.heading("User config:")
        config_user = dict_to_tabulate(
            _config.to_dict(),
            humanize_values=True,
            exclude_attrs=["theme"],
        )
        dict_tabulate(config_user)


@config.command()
@click.argument("keys", type=str, nargs=-1)
@clean_outputs
def get(keys):
    """Get the specific keys from the global configuration.

    Examples:

    \b
    $ polyaxon config get host verify-ssl
    """
    _config = ClientConfigManager.get_config_or_default()

    if not keys:
        return

    print_values = {}
    for key in keys:
        key = key.replace("-", "_")
        if hasattr(_config, key):
            print_values[key] = getattr(_config, key)
        else:
            Printer.print("Key `{}` is not recognised.".format(key))

    dict_tabulate(print_values)


@config.command()
@click.option("--debug", type=bool, help="To set the verbosity of the client.")
@click.option("--host", type=str, help="To set the server endpoint.")
@click.option(
    "--no-api",
    type=bool,
    help="To disable any API call.",
)
@click.option(
    "--verify-ssl",
    type=bool,
    help="To set whether or not to verify the SSL certificate.",
)
@click.option(
    "--home",
    type=click.Path(exists=True),
    help="To set POLYAXON_HOME to specify the context where the CLI/Client reads/writes global configuration.",
)
@click.option(
    "--disable-errors-reporting",
    type=bool,
    help="To set the disable errors reporting.",
)
@click.option(
    "--no-purge",
    is_flag=True,
    default=False,
    help="To reconfigure the host without purging auth and other config options.",
)
@clean_outputs
def set(**kwargs):  # pylint:disable=redefined-builtin
    """Set the global config values.

    Examples:

    \b
    $ polyaxon config set --host=localhost
    """
    if kwargs.get("home") is not None:
        try:
            _config = HomeConfigManager.get_config_or_default()
        except Exception as e:
            logger.debug(
                "Home configuration could not be loaded.\n"
                "Error: %s\n"
                "Purging home configuration and resetting values.",
                e,
            )
            logger.debug()
            HomeConfigManager.purge()
            _config = HomeConfigManager.get_config_or_default()
        setattr(_config, "path", kwargs.get("home"))
        HomeConfigManager.set_config(_config)

    from polyaxon.managers.auth import AuthConfigManager

    try:
        _config = ClientConfigManager.get_config_or_default()
    except Exception as e:
        handle_cli_error(e, message="Polyaxon load configuration.")
        Printer.heading("You can reset your config by running: `polyaxon config purge`")
        sys.exit(1)

    should_purge = False
    for key, value in kwargs.items():
        if key == "host" and value is not None:
            should_purge = True
        if value is not None:
            setattr(_config, key, value)

    ClientConfigManager.set_config(_config)
    Printer.success("Config was updated.")
    # Reset cli config
    CliConfigManager.purge()
    if should_purge and not kwargs.get("no_purge"):
        AuthConfigManager.purge()
        UserConfigManager.purge()
        settings.set_client_config()
        set_versions_config()


@config.command()
@click.option(
    "--cache-only",
    is_flag=True,
    help="To purge the cache only.",
)
@clean_outputs
def purge(cache_only):
    """Purge the global config values."""
    from polyaxon.managers.auth import AuthConfigManager
    from polyaxon.managers.project import ProjectConfigManager
    from polyaxon.managers.run import RunConfigManager

    if not cache_only:
        ClientConfigManager.purge()
        CliConfigManager.purge()
        AuthConfigManager.purge()
        UserConfigManager.purge()
    ProjectConfigManager.purge()
    RunConfigManager.purge()
    Printer.success("Configs was removed.")
