import pytest

from polyaxon.managers.project import ProjectConfigManager
from polyaxon.schemas.responses.v1_project import V1Project
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestProjectConfigManager(BaseTestCase):
    def test_default_props(self):
        assert ProjectConfigManager.is_all_visibility() is True
        assert ProjectConfigManager.IN_PROJECT_DIR is True
        assert ProjectConfigManager.CONFIG_FILE_NAME == ".project"
        assert ProjectConfigManager.CONFIG == V1Project
