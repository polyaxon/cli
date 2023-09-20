import pytest

from polyaxon._managers.project import ProjectConfigManager
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.client import V1Project


@pytest.mark.managers_mark
class TestProjectConfigManager(BaseTestCase):
    def test_default_props(self):
        assert ProjectConfigManager.is_all_visibility() is True
        assert ProjectConfigManager.IN_PROJECT_DIR is True
        assert ProjectConfigManager.CONFIG_FILE_NAME == ".project"
        assert ProjectConfigManager.CONFIG == V1Project
