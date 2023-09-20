import pytest

from polyaxon._managers.agent import AgentConfigManager
from polyaxon._schemas.agent import AgentConfig
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestAgentConfigManager(BaseTestCase):
    def test_default_props(self):
        assert AgentConfigManager.is_global() is True
        assert AgentConfigManager.CONFIG_PATH is None
        assert AgentConfigManager.IN_PROJECT_DIR is False
        assert AgentConfigManager.CONFIG_FILE_NAME == ".agent"
        assert AgentConfigManager.CONFIG == AgentConfig
