from polyaxon.env_vars.getters.owner_entity import resolve_entity_info
from polyaxon.exceptions import PolyaxonClientException, PolyaxonSchemaError
from polyaxon.utils.fqn_utils import get_entity_full_name, get_entity_info
from polyaxon.utils.test_utils import BaseTestCase


class TestOwnerEnvVars(BaseTestCase):
    def test_get_entity_full_name(self):
        assert get_entity_full_name(None) is None
        assert get_entity_full_name("owner", None) is None
        assert get_entity_full_name("owner", "entity") == "owner/entity"

    def test_get_entity_info(self):
        with self.assertRaises(PolyaxonSchemaError):
            get_entity_info(None)

        with self.assertRaises(PolyaxonSchemaError):
            get_entity_info("")

        with self.assertRaises(PolyaxonSchemaError):
            get_entity_info("foo.bar.moo")

        with self.assertRaises(PolyaxonSchemaError):
            get_entity_info("foo/bar/moo")

        assert get_entity_info("entity") == (None, "entity")
        assert get_entity_info("owner.entity") == ("owner", "entity")
        assert get_entity_info("owner/entity") == ("owner", "entity")

    def test_resolve_entity_info(self):
        with self.assertRaises(PolyaxonClientException):
            resolve_entity_info("", "")

        with self.assertRaises(PolyaxonClientException):
            resolve_entity_info("", "test")

        with self.assertRaises(PolyaxonClientException):
            resolve_entity_info(None, None)

        with self.assertRaises(PolyaxonSchemaError):
            resolve_entity_info("owner.entity.test", "")

        with self.assertRaises(PolyaxonSchemaError):
            resolve_entity_info("owner/entity/test", "")

        assert resolve_entity_info("owner.entity", "project") == ("owner", "entity")
