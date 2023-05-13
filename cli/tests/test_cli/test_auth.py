import pytest

from mock import patch

from polyaxon.cli.auth import logout, whoami
from tests.test_cli.utils import BaseCommandTestCase


@pytest.mark.cli_mark
class TestCliAuth(BaseCommandTestCase):
    @patch("polyaxon.managers.auth.AuthConfigManager.purge")
    @patch("polyaxon.managers.user.UserConfigManager.purge")
    def test_logout(self, get_user, get_auth):
        self.runner.invoke(logout)
        assert get_auth.call_count == 1
        assert get_user.call_count == 1

    @patch("polyaxon.sdk.api.UsersV1Api.get_user")
    def test_whoami(self, get_user):
        self.runner.invoke(whoami)
        assert get_user.call_count == 1
