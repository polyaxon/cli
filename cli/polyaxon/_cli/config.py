import sys

import click

from clipped.formatting import Printer
from clipped.utils.dicts import dict_to_tabulate
from clipped.utils.paths import check_or_create_path

from polyaxon import settings
from polyaxon._cli.errors import handle_cli_error
from polyaxon._cli.session import set_versions_config
from polyaxon._managers.cli import CliConfigManager
from polyaxon._managers.client import ClientConfigManager
from polyaxon._managers.home import HomeConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon.logger import clean_outputs, logger


def set_home_path(home_path: str):
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
    try:
        check_or_create_path(home_path, is_dir=False)
    except Exception as e:
        handle_cli_error(
            e, message=f"Couldn't create path configuration at {home_path}."
        )
        Printer.heading(
            "Please make sure that that the path is accessible or manually create it."
        )
        sys.exit(1)
    setattr(_config, "path", home_path)
    HomeConfigManager.set_config(_config)
    settings.set_home_config(_config)


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
            _config,
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
    $ polyaxon config get home host verify-ssl
    """

    if not keys:
        return

    keys = set(keys)

    # Check Home config
    _config = HomeConfigManager.get_config_or_default()
    print_values = {}
    if "home" in keys:
        if hasattr(_config, "path"):
            print_values["home"] = getattr(_config, "path")
            keys.discard("home")
    if print_values:
        Printer.heading("Home config:")
        Printer.dict_tabulate(print_values)

    not_found_keys = set([])

    # Check client config
    _config = ClientConfigManager.get_config_or_default()
    print_values = {}
    for key in keys:
        key = key.replace("-", "_")
        if hasattr(_config, key):
            print_values[key] = getattr(_config, key)
            not_found_keys.discard(key)
        else:
            not_found_keys.add(key)
    if print_values:
        Printer.heading("Client config:")
        Printer.dict_tabulate(print_values)

    keys = not_found_keys
    not_found_keys = set([])

    # Check cli config
    _config = CliConfigManager.get_config_or_default()
    print_values = {}
    for key in keys:
        key = key.replace("-", "_")
        if hasattr(_config, key):
            print_values[key] = getattr(_config, key)
            not_found_keys.discard(key)
        else:
            not_found_keys.add(key)
    if print_values:
        Printer.heading("CLI config:")
        Printer.dict_tabulate(print_values)

    if not_found_keys:
        Printer.print(
            "The following keys `{}` were not found in any configuration.".format(
                not_found_keys
            )
        )


@config.command(name="set")
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
    type=click.Path(exists=False),
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
def set_(**kwargs):  # pylint:disable=redefined-builtin
    """Set the global config values.

    Examples:

    \b
    $ polyaxon config set --home=/tmp/.polyaxon

    \b
    $ polyaxon config set --home=

    \b
    $ polyaxon config set --host=localhost
    """
    no_purge = kwargs.pop("no_purge", None)
    if kwargs.get("home") is not None:
        home_path = kwargs.pop("home", None)
        set_home_path(home_path)

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
