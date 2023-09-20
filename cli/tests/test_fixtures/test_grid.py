import pytest

from polyaxon._flow import V1Operation
from polyaxon._utils.fixtures import get_fxt_grid_with_inputs_outputs
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.fixtures_mark
class TestGridsFixtures(BaseTestCase):
    def test_fxt_grid_with_inputs_outputs(self):
        config = get_fxt_grid_with_inputs_outputs()
        assert V1Operation.read(config).to_dict() == config
