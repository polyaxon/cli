import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict

from polyaxon.polyflow.notifications import V1Notification
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.plugins_mark
class TestNotificationsConfigs(BaseTestCase):
    def test_notifications_config(self):
        # Add auth
        config_dict = {}

        with self.assertRaises(ValidationError):
            V1Notification.from_dict(config_dict)

        # Add connection
        config_dict["connections"] = ["test"]
        config = V1Notification.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())

        # Add a trigger policy
        config_dict["trigger"] = "not-supported"
        with self.assertRaises(ValidationError):
            V1Notification.from_dict(config_dict)

        # Add outputs
        config_dict["trigger"] = "succeeded"
        config = V1Notification.from_dict(config_dict)
        assert_equal_dict(config_dict, config.to_dict())
