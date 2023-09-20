import os
import pytest
import uuid

from datetime import timedelta
from mock import patch

from clipped.utils.tz import now

from polyaxon._managers.cli import CliConfigManager
from polyaxon._schemas.cli import CliConfig
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.managers_mark
class TestCliConfigManager(BaseTestCase):
    def test_default_props(self):
        assert CliConfigManager.is_global() is True
        assert CliConfigManager.IN_PROJECT_DIR is False
        assert CliConfigManager.CONFIG_FILE_NAME == ".cli"
        assert CliConfigManager.CONFIG == CliConfig


@pytest.mark.managers_mark
class TestCliConfigManagerMethods(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.filename = uuid.uuid4().hex
        CliConfigManager.CONFIG_FILE_NAME = self.filename

    def tearDown(self):
        path = CliConfigManager.get_config_filepath(create=False)
        if not os.path.exists(path):
            return
        os.remove(path)

    def test_set_compatibility(self):
        config = CliConfigManager.get_config_or_default()
        assert config.current_version is None
        config = CliConfigManager.reset(current_version="1.2.3")
        assert config.current_version == "1.2.3"

    def test_should_check(self):
        with patch.object(CliConfigManager, "reset") as patch_fct:
            result = CliConfigManager.should_check()

        assert patch_fct.call_count == 1
        assert result is True

        CliConfigManager.reset(
            last_check=now(),
            current_version="0.0.5",
            installation={"key": "uuid", "version": "1.1.4-rc11", "dist": "foo"},
            compatibility={"cli": {"min": "0.0.4", "latest": "1.1.4"}},
        )
        with patch.object(CliConfigManager, "reset") as patch_fct:
            result = CliConfigManager.should_check()

        assert patch_fct.call_count == 0
        assert result is False

        CliConfigManager.reset(
            last_check=now() - timedelta(seconds=10000),
            current_version="0.0.5",
            installation={"key": "uuid", "version": "1.1.4-rc11", "dist": "foo"},
            compatibility={"cli": {"min": "0.0.4", "latest": "1.1.4"}},
        )
        with patch.object(CliConfigManager, "reset") as patch_fct:
            result = CliConfigManager.should_check()

        assert patch_fct.call_count == 1
        assert result is True

        CliConfigManager.reset(
            last_check=now(),
            current_version="0.0.2",
            installation={"key": "uuid", "version": "1.1.4-rc11", "dist": "foo"},
            compatibility={"cli": {"min": "0.0.4", "latest": "1.1.4"}},
        )
        with patch.object(CliConfigManager, "reset") as patch_fct:
            result = CliConfigManager.should_check()

        # Although condition for showing a message, do not reset
        assert patch_fct.call_count == 0
        assert result is False
