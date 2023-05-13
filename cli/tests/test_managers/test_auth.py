import pytest

from polyaxon.managers.auth import AuthConfigManager
from polyaxon.schemas.api.authentication import AccessTokenConfig
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestAuthConfigManager(BaseTestCase):
    def test_default_props(self):
        assert AuthConfigManager.is_global() is True
        assert AuthConfigManager.is_local() is False
        assert AuthConfigManager.IN_PROJECT_DIR is False
        assert AuthConfigManager.CONFIG_FILE_NAME == ".auth"
        assert AuthConfigManager.CONFIG == AccessTokenConfig
