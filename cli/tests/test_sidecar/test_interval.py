from polyaxon.sidecar.container.intervals import get_sync_interval
from polyaxon.utils.test_utils import BaseTestCase


class TestSidecar(BaseTestCase):
    def test_get_interval_counter(self):
        assert get_sync_interval(0, 0) == -1
        assert get_sync_interval(1, 2) == 0
        assert get_sync_interval(2, 2) == 2
        assert get_sync_interval(3, 2) == 2
        assert get_sync_interval(4, 2) == 3
        assert get_sync_interval(4, 2) == 3
        assert get_sync_interval(6, 2) == 4
