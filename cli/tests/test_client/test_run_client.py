import pytest
import uuid

from mock import mock

from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.client import RunClient


@pytest.mark.client_mark
class TestRunClient(BaseTestCase):
    @mock.patch("polyaxon._sdk.api.RunsV1Api.patch_run")
    def test_get_statuses(self, sdk_patch_run):
        client = RunClient(owner="owner", project="project", run_uuid=uuid.uuid4().hex)
        assert client.run_data.tags is None
        client.log_tags(["foo", "bar"])
        assert client.run_data.tags == ["foo", "bar"]
        assert sdk_patch_run.call_count == 1
