import pytest

from clipped.utils.assertions import assert_equal_dict

from polyaxon._flow.termination import V1Termination
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.termination_mark
class TestV1Terminations(BaseTestCase):
    def test_termination_config(self):
        config_dict = {}
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        config_dict["maxRetries"] = "{{ fs }}"
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add max_retries
        config_dict["maxRetries"] = 4
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add timeout
        config_dict["timeout"] = 4
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add ttl
        config_dict["ttl"] = 40
        config = V1Termination.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())
