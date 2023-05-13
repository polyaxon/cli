import pytest

from polyaxon.managers.run import RunConfigManager
from polyaxon.schemas.responses.v1_run import V1Run
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestRunConfigManager(BaseTestCase):
    def test_default_props(self):
        assert RunConfigManager.is_all_visibility() is True
        assert RunConfigManager.IN_PROJECT_DIR is True
        assert RunConfigManager.CONFIG_FILE_NAME == ".run"
        assert RunConfigManager.CONFIG == V1Run
