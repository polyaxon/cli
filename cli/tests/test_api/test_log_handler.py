import pytest

from polyaxon._schemas.log_handler import V1LogHandler
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.api_mark
class TestV1LogHandler(BaseTestCase):
    def test_log_handler_config(self):
        config_dict = {"dsn": "https//foo:bar", "environment": "staging"}
        config = V1LogHandler.from_dict(config_dict)
        assert config.to_dict() == config_dict
