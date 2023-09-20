import pytest

from uuid import uuid4

from polyaxon._flow import V1Operation
from polyaxon._utils.fixtures import (
    get_fxt_job_with_hub_ref,
    get_fxt_service,
    get_fxt_service_with_inputs,
    get_fxt_service_with_upstream_runs,
)
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.fixtures_mark
class TestServicesFixtures(BaseTestCase):
    def test_fxt_service(self):
        config = get_fxt_service()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_service_with_inputs(self):
        config = get_fxt_service_with_inputs()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_service_with_upstream_runs(self):
        config = get_fxt_service_with_upstream_runs(uuid4())
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_job_with_hub_ref(self):
        config = get_fxt_job_with_hub_ref()
        assert V1Operation.read(config).to_dict() == config
