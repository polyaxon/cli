import pytest

from polyaxon._managers.home import HomeConfigManager
from polyaxon._schemas.home import HomeConfig
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestHomeConfigManager(BaseTestCase):
    def test_default_props(self):
        assert HomeConfigManager.is_global() is True
        assert HomeConfigManager.is_local() is False
        assert HomeConfigManager.IN_PROJECT_DIR is False
        assert HomeConfigManager.CONFIG_FILE_NAME == ".home"
        assert HomeConfigManager.CONFIG == HomeConfig
