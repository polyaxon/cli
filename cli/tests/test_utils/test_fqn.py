import pytest

from unittest import TestCase

from polyaxon._utils.fqn_utils import (
    get_entity_full_name,
    get_entity_info,
    get_versioned_entity_full_name,
)
from polyaxon.exceptions import PolyaxonSchemaError


@pytest.mark.utils_mark
class TestEnvVars(TestCase):
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
        assert get_entity_info("owner.team.entity") == ("owner/team", "entity")
        assert get_entity_info("owner/entity") == ("owner", "entity")
        assert get_entity_info("owner/team/entity") == ("owner/team", "entity")

    def test_get_versioned_entity_full_name(self):
        assert get_versioned_entity_full_name(None, None) is None
        assert get_versioned_entity_full_name(None, "hub") == "hub"
        assert get_versioned_entity_full_name(None, "hub", tag="ver") == "hub:ver"
        assert get_versioned_entity_full_name("owner", "hub") == "owner/hub"
        assert get_versioned_entity_full_name("owner", "hub", "ver") == "owner/hub:ver"
