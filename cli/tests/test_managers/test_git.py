import pytest

from polyaxon.managers.git import GitConfigManager
from polyaxon.polyflow import V1Init
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestGitConfigManager(BaseTestCase):
    def test_default_props(self):
        assert GitConfigManager.is_global() is False
        assert GitConfigManager.is_local() is True
        assert GitConfigManager.IN_PROJECT_DIR is False
        assert GitConfigManager.CONFIG_FILE_NAME == "polyaxongit.yaml"
        assert GitConfigManager.CONFIG == V1Init
