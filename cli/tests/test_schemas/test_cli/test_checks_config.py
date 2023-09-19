import os
import pytest
import tempfile

from datetime import timedelta

from clipped.utils.tz import now

from polyaxon.env_vars.keys import ENV_KEYS_INTERVALS_COMPATIBILITY_CHECK
from polyaxon.schemas.checks import ChecksConfig
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.schemas_mark
class TestChecksConfig(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.filename = "{}/{}".format(tempfile.mkdtemp(), "config")

    def test_get_interval(self):
        config = ChecksConfig()
        assert config.get_interval(1) == 1
        assert config.get_interval(-1) == -1
        assert config.get_interval(-2) == -2
        assert config.get_interval() == ChecksConfig._INTERVAL
        os.environ[ENV_KEYS_INTERVALS_COMPATIBILITY_CHECK] = "-1"
        assert config.get_interval() == -1
        os.environ[ENV_KEYS_INTERVALS_COMPATIBILITY_CHECK] = "-2"
        assert config.get_interval() == ChecksConfig._INTERVAL
        os.environ[ENV_KEYS_INTERVALS_COMPATIBILITY_CHECK] = "1"
        assert config.get_interval() == ChecksConfig._INTERVAL
        os.environ[ENV_KEYS_INTERVALS_COMPATIBILITY_CHECK] = str(
            ChecksConfig._INTERVAL + 1
        )
        assert config.get_interval() == ChecksConfig._INTERVAL + 1

    def test_should_check(self):
        config = ChecksConfig(last_check=now())
        assert config.should_check(-1) is False
        assert config.should_check(0) is True

        config.last_check = now() - timedelta(seconds=10000)
        assert config.should_check(-1) is False
        assert config.should_check() is True
        assert config.should_check(100) is True
        assert config.should_check(100000) is False
