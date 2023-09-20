import pytest

from polyaxon._flow import V1HpDateRange, V1Operation
from polyaxon._utils.fixtures.backfill import get_fxt_backfill_with_inputs_outputs
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.fixtures_mark
class TestBackfillsFixtures(BaseTestCase):
    def test_fxt_backfill_with_inputs_outputs(self):
        config = get_fxt_backfill_with_inputs_outputs()
        result = V1Operation.read(config).to_dict()
        assert result == config
