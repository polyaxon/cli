import pytest

from polyaxon._managers.run import RunConfigManager
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.client import V1Run


@pytest.mark.managers_mark
class TestRunConfigManager(BaseTestCase):
    def test_default_props(self):
        assert RunConfigManager.is_all_visibility() is True
        assert RunConfigManager.IN_PROJECT_DIR is True
        assert RunConfigManager.CONFIG_FILE_NAME == ".run"
        assert RunConfigManager.CONFIG == V1Run
