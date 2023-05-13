import pytest
import uuid

from mock import MagicMock, mock

from polyaxon import settings
from polyaxon.client import RunClient
from polyaxon.lifecycle import V1Statuses
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.client_mark
class TestStatuses(BaseTestCase):
    @mock.patch("polyaxon.sdk.api.RunsV1Api.get_run_statuses")
    def test_get_statuses(self, sdk_get_run_statuses):
        client = RunClient(owner="owner", project="project", run_uuid=uuid.uuid4().hex)
        for _ in client.get_statuses():
            pass
        assert sdk_get_run_statuses.call_count == 1

    @mock.patch("polyaxon.sdk.api.RunsV1Api.get_run_statuses")
    def test_get_statuses_watch(self, sdk_get_run_statuses):
        settings.CLIENT_CONFIG.watch_interval = 1
        client = RunClient(owner="owner", project="project", run_uuid=uuid.uuid4().hex)
        sdk_get_run_statuses.return_value = MagicMock(
            status=V1Statuses.RUNNING, status_conditions=[]
        )
        for _ in client.watch_statuses():
            sdk_get_run_statuses.return_value = MagicMock(
                status=V1Statuses.FAILED, status_conditions=[]
            )
        assert sdk_get_run_statuses.call_count == 2
