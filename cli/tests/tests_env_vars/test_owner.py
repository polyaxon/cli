from polyaxon._env_vars.getters.owner_entity import resolve_entity_info
from polyaxon._utils.fqn_utils import get_entity_full_name, get_entity_info
from polyaxon._utils.test_utils import BaseTestCase
from polyaxon.exceptions import PolyaxonClientException, PolyaxonSchemaError


class TestOwnerEnvVars(BaseTestCase):
    def test_get_entity_full_name(self):
        assert get_entity_full_name(None) is None
        assert get_entity_full_name("owner", None) is None
        assert get_entity_full_name("owner", "entity") == "owner/entity"
        assert get_entity_full_name("owner/team", "entity") == "owner/entity"

    def test_get_entity_info(self):
        with self.assertRaises(PolyaxonSchemaError):
            get_entity_info(None)

        with self.assertRaises(PolyaxonSchemaError):
            get_entity_info("")

        with self.assertRaises(PolyaxonSchemaError):
            get_entity_info("foo.bar.moo.mar")

        with self.assertRaises(PolyaxonSchemaError):
            get_entity_info("foo/bar/moo/mar")

        assert get_entity_info("entity") == (None, "entity")
        assert get_entity_info("owner.entity") == ("owner", "entity")
        assert get_entity_info("owner/entity") == ("owner", "entity")
        assert get_entity_info("owner/team/entity") == ("owner/team", "entity")

    def test_resolve_entity_info(self):
        with self.assertRaises(PolyaxonClientException):
            resolve_entity_info("", "")

        with self.assertRaises(PolyaxonClientException):
            resolve_entity_info("", "test")

        with self.assertRaises(PolyaxonClientException):
            resolve_entity_info(None, None)

        with self.assertRaises(PolyaxonSchemaError):
            resolve_entity_info("owner.entity.test.foo", "")

        with self.assertRaises(PolyaxonSchemaError):
            resolve_entity_info("owner/entity/test/foo", "")

        assert resolve_entity_info("owner.entity", "project") == (
            "owner",
            None,
            "entity",
        )
        assert resolve_entity_info("owner.team.entity", "project") == (
            "owner",
            "team",
            "entity",
        )
