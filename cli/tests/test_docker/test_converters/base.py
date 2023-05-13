import pytest

from polyaxon.docker.converter.converters.job import JobConverter
from polyaxon.utils.test_utils import BaseTestCase


class DummyConverter(JobConverter):
    SPEC_KIND = "dumy"
    MAIN_CONTAINER_ID = "dummy"


@pytest.mark.converter_mark
class BaseConverterTest(BaseTestCase):
    SET_AGENT_SETTINGS = True

    def setUp(self):
        super().setUp()
        self.converter = DummyConverter(
            owner_name="owner-name",
            project_name="project-name",
            run_name="run-name",
            run_uuid="run_uuid",
        )
