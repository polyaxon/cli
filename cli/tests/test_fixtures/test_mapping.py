import pytest

from polyaxon.polyflow import V1Operation
from polyaxon.utils.fixtures import (
    get_fxt_mapping_with_inputs_outputs,
    get_fxt_mapping_with_run_patch,
)
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.fixtures_mark
class TestMappingsFixtures(BaseTestCase):
    def test_fxt_mapping_with_inputs_outputs(self):
        config = get_fxt_mapping_with_inputs_outputs()
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_mapping_with_run_patch(self):
        config = get_fxt_mapping_with_run_patch()
        assert V1Operation.read(config).to_dict() == config
