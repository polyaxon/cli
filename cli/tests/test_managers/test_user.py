import pytest

from polyaxon._managers.user import UserConfigManager
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.client import V1User


@pytest.mark.managers_mark
class TestUserConfigManager(BaseTestCase):
    def test_default_props(self):
        assert UserConfigManager.is_global() is True
        assert UserConfigManager.IN_PROJECT_DIR is True
        assert UserConfigManager.CONFIG_FILE_NAME == ".user"
        assert UserConfigManager.CONFIG == V1User
