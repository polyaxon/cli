import pytest

from polyaxon._managers.auth import AuthConfigManager
from polyaxon._schemas.authentication import AccessTokenConfig
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestAuthConfigManager(BaseTestCase):
    def test_default_props(self):
        assert AuthConfigManager.is_global() is True
        assert AuthConfigManager.is_local() is False
        assert AuthConfigManager.IN_PROJECT_DIR is False
        assert AuthConfigManager.CONFIG_FILE_NAME == ".auth"
        assert AuthConfigManager.CONFIG == AccessTokenConfig
