from polyaxon.env_vars.getters import get_component_info
from polyaxon.exceptions import PolyaxonSchemaError
from polyaxon.utils.test_utils import BaseTestCase


class TestComponentEnvVars(BaseTestCase):
    def test_get_component_info(self):
        with self.assertRaises(PolyaxonSchemaError):
            get_component_info(None)

        with self.assertRaises(PolyaxonSchemaError):
            get_component_info("")

        assert get_component_info("hub") == ("polyaxon", "hub", "latest")
        assert get_component_info("hub:ver") == ("polyaxon", "hub", "ver")
        assert get_component_info("owner.hub") == ("owner", "hub", "latest")
        assert get_component_info("owner/hub") == ("owner", "hub", "latest")
        assert get_component_info("owner.hub:ver") == ("owner", "hub", "ver")
        assert get_component_info("owner/hub:ver") == ("owner", "hub", "ver")
