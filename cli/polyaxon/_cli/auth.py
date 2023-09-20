import sys

import click

from clipped.formatting import Printer
from clipped.utils.dicts import dict_to_tabulate
from urllib3.exceptions import HTTPError

from polyaxon import settings
from polyaxon._cli.dashboard import get_dashboard_url
from polyaxon._cli.errors import handle_cli_error, handle_command_not_in_ce, not_in_ce
from polyaxon._cli.session import (
    ensure_cli_config,
    session_expired,
    set_versions_config,
)
from polyaxon._managers.auth import AuthConfigManager
from polyaxon._managers.cli import CliConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon._schemas.authentication import AccessTokenConfig, V1Credentials
from polyaxon._sdk.schemas.v1_auth import V1Auth
from polyaxon._sdk.schemas.v1_user import V1User
from polyaxon.client import PolyaxonClient
from polyaxon.exceptions import ApiException
from polyaxon.logger import clean_outputs, logger


def get_user_info(user: V1User):
    response = dict_to_tabulate(user.to_dict(), exclude_attrs=["role", "theme"])
    Printer.heading("User info:")
    Printer.dict_tabulate(response)


@click.command()
@click.option("--token", "-t", help="Polyaxon token.")
@click.option("--username", "-u", help="Polyaxon username or email.")
@click.option("--password", "-p", help="Polyaxon password.")
@clean_outputs
def login(token, username, password):
    """Login to Polyaxon Cloud or Polyaxon EE."""
    polyaxon_client = PolyaxonClient()
    ensure_cli_config()

    if not settings.CLI_CONFIG or settings.CLI_CONFIG.is_community:
        handle_command_not_in_ce()

    if username and not token:
        # Use user or email / password login
        if not password:
            password = click.prompt(
                "Please enter your password", type=str, hide_input=True
            )
            password = password.strip()
            if not password:
                logger.info(
                    "You entered an empty string. "
                    "Please make sure you enter your password correctly."
                )
                sys.exit(1)

        try:
            body = V1Credentials(username=username, password=password)
            access_auth = polyaxon_client.auth_v1.login(body=body)
        except (ApiException, HTTPError) as e:
            AuthConfigManager.purge()
            UserConfigManager.purge()
            CliConfigManager.purge()
            handle_cli_error(e, message="Could not login.")
            sys.exit(1)

        if not access_auth.token:
            Printer.error("Failed to login")
            return
    else:
        if not token:
            token_url = get_dashboard_url(subpath="profile/token")
            click.confirm(
                "Authentication token page will now open in your browser. Continue?",
                abort=True,
                default=True,
            )

            click.launch(token_url)
            logger.info("Please copy and paste the authentication token.")
            token = click.prompt(
                "This is an invisible field. Paste token and press ENTER",
                type=str,
                hide_input=True,
            )

        if not token:
            logger.info(
                "Empty token received. "
                "Make sure your shell is handling the token appropriately."
            )
            logger.info(
                "See docs for help: http://polyaxon.com/docs/polyaxon_cli/commands/auth"
            )
            return

        access_auth = V1Auth(token=token.strip(" "))

    # Set user
    try:
        AuthConfigManager.purge()
        UserConfigManager.purge()
        polyaxon_client = PolyaxonClient(token=access_auth.token)
        user = polyaxon_client.users_v1.get_user()
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not load user info.")
        sys.exit(1)
    access_token = AccessTokenConfig(username=user.username, token=access_auth.token)
    AuthConfigManager.set_config(access_token)
    UserConfigManager.set_config(user)
    polyaxon_client.config.token = access_auth.token
    Printer.success("Login successful")
    get_user_info(user)

    set_versions_config(polyaxon_client=polyaxon_client, set_handler=True)


@click.command()
@clean_outputs
def logout():
    """Logout from Polyaxon Cloud or Polyaxon EE."""
    AuthConfigManager.purge()
    UserConfigManager.purge()
    CliConfigManager.purge()
    Printer.success("You are logged out")


@click.command()
@not_in_ce
@clean_outputs
def whoami():
    """Show current logged Polyaxon Cloud or Polyaxon EE user."""
    try:
        polyaxon_client = PolyaxonClient()
        user = polyaxon_client.users_v1.get_user()
        get_user_info(user)
    except ApiException as e:
        if e.status == 403:
            session_expired()
        handle_cli_error(e, message="Could not get the user info.", sys_exit=True)
    except (ApiException, HTTPError) as e:
        handle_cli_error(e, message="Could not load user info.", sys_exit=True)
