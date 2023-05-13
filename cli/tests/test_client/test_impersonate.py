import os
import pytest
import tempfile
import uuid

from mock import patch
from unittest.mock import MagicMock

from polyaxon.client.impersonate import create_context_auth, impersonate
from polyaxon.schemas.api.authentication import AccessTokenConfig
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.client_mark
class TestImpersonate(BaseTestCase):
    def test_create_context_auth(self):
        token = uuid.uuid4().hex
        context_mount = tempfile.mkdtemp()
        context_mount_auth = "{}/.auth".format(context_mount)

        # Login without updating the token and without persistence
        if os.path.exists(context_mount_auth):
            os.remove(context_mount_auth)

        assert os.path.exists(context_mount_auth) is False
        create_context_auth(AccessTokenConfig(token=token), context_mount_auth)
        assert os.path.exists(context_mount_auth) is True

    @patch("polyaxon.sdk.api.RunsV1Api.impersonate_token")
    @patch("polyaxon.sdk.api.UsersV1Api.get_user")
    @patch("polyaxon.client.impersonate.create_context_auth")
    def test_login_impersonate(self, create_context, get_user, impersonate_token):
        get_user.return_value = MagicMock(username="foobar", email="foo@bar.com")
        impersonate_token.return_value = MagicMock(token="token")
        impersonate(owner="owner", project="project", run_uuid=uuid.uuid4().hex)
        assert impersonate_token.call_count == 1
        assert get_user.call_count == 1
        assert create_context.call_count == 1
