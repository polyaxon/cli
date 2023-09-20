import pytest

from polyaxon._flow import V1Operation
from polyaxon._utils.fixtures import (
    get_fxt_bo_with_inputs_outputs,
    get_fxt_bo_with_run_patch,
)
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.fixtures_mark
class TestBoFixtures(BaseTestCase):
    def test_fxt_bo_with_inputs_outputs(self):
        config = get_fxt_bo_with_inputs_outputs(tuner="foo/bar")
        assert V1Operation.read(config).to_dict() == config

    def test_fxt_bo_with_run_patch(self):
        config = get_fxt_bo_with_run_patch()
        assert V1Operation.read(config).to_dict() == config
