import sys

import click

from clipped.formatting import Printer
from clipped.utils.dicts import dict_to_tabulate

from polyaxon import settings
from polyaxon._cli.errors import handle_cli_error
from polyaxon._cli.session import set_versions_config
from polyaxon._managers.cli import CliConfigManager
from polyaxon._managers.client import ClientConfigManager
from polyaxon._managers.home import HomeConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon.logger import clean_outputs, logger


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
    Printer.dict_tabulate(_config.to_dict())
    _config = ClientConfigManager.get_config_or_default()
    Printer.heading("Client config:")
    Printer.dict_tabulate(_config.to_dict())
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
            Printer.dict_tabulate(config_installation)
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
        Printer.dict_tabulate(config_user)


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

    Printer.dict_tabulate(print_values)


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
    no_purge = kwargs.pop("no_purge", None)
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
        setattr(_config, "path", kwargs.pop("home", None))
        HomeConfigManager.set_config(_config)

    from polyaxon._managers.auth import AuthConfigManager

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
    if should_purge and not no_purge:
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
    from polyaxon._managers.auth import AuthConfigManager
    from polyaxon._managers.project import ProjectConfigManager
    from polyaxon._managers.run import RunConfigManager

    if not cache_only:
        ClientConfigManager.purge()
        CliConfigManager.purge()
        AuthConfigManager.purge()
        UserConfigManager.purge()
    ProjectConfigManager.purge()
    RunConfigManager.purge()
    Printer.success("Configs was removed.")
