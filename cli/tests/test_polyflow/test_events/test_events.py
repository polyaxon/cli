import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict

from polyaxon.polyflow import V1EventKind, V1EventTrigger
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.events_mark
class TestEventTriggerConfigs(BaseTestCase):
    def test_events_config(self):
        config_dict = {}

        with self.assertRaises(ValidationError):
            V1EventTrigger.from_dict(config_dict)

        config_dict["ref"] = "test"
        with self.assertRaises(ValidationError):
            V1EventTrigger.from_dict(config_dict)

        # Add kinds
        config_dict["kinds"] = [V1EventKind.RUN_STATUS_DONE]
        config = V1EventTrigger.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Set correct ref
        config_dict["ref"] = "ops.A"
        config = V1EventTrigger.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add another event
        config_dict["kinds"] = [
            V1EventKind.RUN_STATUS_RESUMING,
            V1EventKind.RUN_NEW_ARTIFACTS,
        ]
        V1EventTrigger.from_dict(config_dict)

        # Use run event
        config_dict["ref"] = "runs.0de53b5bf8b04a219d12a39c6b92bcce"
        config = V1EventTrigger.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())
