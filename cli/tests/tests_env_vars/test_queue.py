from polyaxon._env_vars.getters.queue import get_queue_info
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonSchemaError


class TestQueueEnvVars(BaseTestCase):
    def test_get_queue_info(self):
        with self.assertRaises(PolyaxonSchemaError):
            get_queue_info(None)

        with self.assertRaises(PolyaxonSchemaError):
            get_queue_info("")

        with self.assertRaises(PolyaxonSchemaError):
            get_queue_info("foo/bar/noo")

        with self.assertRaises(PolyaxonSchemaError):
            get_queue_info("foo.bar.noo")

        assert get_queue_info("test") == (None, "test")
        assert get_queue_info("agent.queue") == ("agent", "queue")
        assert get_queue_info("agent/queue") == ("agent", "queue")
