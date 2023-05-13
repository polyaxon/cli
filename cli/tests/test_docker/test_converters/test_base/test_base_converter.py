import pytest

from polyaxon.docker.converter.base import BaseConverter
from polyaxon.exceptions import PolyaxonConverterError
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.converter_mark
class TestConverter(BaseTestCase):
    def setUp(self):
        class DummyConverter(BaseConverter):
            SPEC_KIND = "dummy"
            MAIN_CONTAINER_ID = "dummy"

        self.converter = DummyConverter(
            owner_name="foo", project_name="p1", run_name="j1", run_uuid="uuid"
        )
        super().setUp()

    def test_is_valid(self):
        class Converter(BaseConverter):
            pass

        with self.assertRaises(PolyaxonConverterError):
            Converter(
                owner_name="foo", project_name="test", run_name="test", run_uuid="uuid"
            )

    def test_run_instance(self):
        assert self.converter.run_instance == "foo.p1.runs.uuid"
