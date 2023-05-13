import pytest

from polyaxon.managers.user import UserConfigManager
from polyaxon.schemas.responses.v1_user import V1User
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestUserConfigManager(BaseTestCase):
    def test_default_props(self):
        assert UserConfigManager.is_global() is True
        assert UserConfigManager.IN_PROJECT_DIR is True
        assert UserConfigManager.CONFIG_FILE_NAME == ".user"
        assert UserConfigManager.CONFIG == V1User
