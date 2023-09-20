import uuid

from clipped.utils.tz import now

from polyaxon._notifiers import NotificationSpec
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.schemas import StatusColor, V1StatusCondition, V1Statuses


class TestNotificationSpec(BaseTestCase):
    def test_notification_spec(self):
        uid = uuid.uuid4().hex
        notification = NotificationSpec.load_from_data(
            kind="run",
            owner="onwer",
            project="project",
            uuid=uid,
            name="test",
            status=V1Statuses.FAILED,
            condition=V1StatusCondition(
                type=V1Statuses.FAILED,
                reason="reason",
                message="message",
                last_update_time=now(),
                last_transition_time=now(),
            ),
            wait_time=None,
            duration=None,
            inputs=None,
            outputs=None,
        )
        assert notification.title == "test ({}) Status: {}\n".format(
            uid, V1Statuses.FAILED
        )
        assert notification.description == "reason"
        assert notification.fallback == V1Statuses.FAILED
        assert notification.color == StatusColor.get_color(V1Statuses.FAILED)
        assert notification.url.scheme == "http"
