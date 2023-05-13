import os
import pytest
import uuid

from mock import patch
from mock.mock import MagicMock

from polyaxon import settings
from polyaxon.env_vars.keys import EV_KEYS_RUN_INSTANCE
from polyaxon.exceptions import PolyaxonContainerException
from polyaxon.init.auth import create_auth_context
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.init_mark
class TestInitAuth(BaseTestCase):
    def test_raise_if_env_var_not_found(self):
        with self.assertRaises(PolyaxonContainerException):
            create_auth_context()

    def test_raise_if_env_var_not_correct(self):
        os.environ[EV_KEYS_RUN_INSTANCE] = "foo"
        with self.assertRaises(PolyaxonContainerException):
            create_auth_context()
        del os.environ[EV_KEYS_RUN_INSTANCE]

    @patch("polyaxon.sdk.api.RunsV1Api.impersonate_token")
    @patch("polyaxon.sdk.api.UsersV1Api.get_user")
    @patch("polyaxon.client.impersonate.create_context_auth")
    def test_init_auth(self, create_context, get_user, impersonate_token):
        get_user.return_value = MagicMock(username="foobar", email="foo@bar.com")
        impersonate_token.return_value = MagicMock(token="token")
        settings.CLIENT_CONFIG.is_managed = True
        os.environ[EV_KEYS_RUN_INSTANCE] = "owner.project.runs.{}".format(
            uuid.uuid4().hex
        )
        create_auth_context()
        assert impersonate_token.call_count == 1
        assert create_context.call_count == 1
        assert get_user.call_count == 1
        del os.environ[EV_KEYS_RUN_INSTANCE]
        settings.CLIENT_CONFIG.is_managed = None
