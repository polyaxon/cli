import pytest

from polyaxon._containers.names import (
    INIT_ARTIFACTS_CONTAINER_PREFIX,
    INIT_GIT_CONTAINER_PREFIX,
    MAX_CONTAINER_NAME_LENGTH,
    generate_container_name,
    sanitize_container_name,
)
from polyaxon._utils.test_utils import BaseTestCase

LONG_CONNECTION_NAME = "very-long-artifacts-store-connection-name-for-the-team"


@pytest.mark.converter_mark
class TestContainerNames(BaseTestCase):
    def test_generate_container_name_short_suffix_is_untouched(self):
        name = generate_container_name(
            INIT_ARTIFACTS_CONTAINER_PREFIX, "s3-store", False
        )
        assert name == "polyaxon-init-artifacts-s3-store"

    def test_generate_container_name_replaces_underscores(self):
        name = generate_container_name(
            INIT_ARTIFACTS_CONTAINER_PREFIX, "my_store", False
        )
        assert name == "polyaxon-init-artifacts-my-store"

    def test_generate_container_name_respects_k8s_limit(self):
        for prefix in (
            INIT_ARTIFACTS_CONTAINER_PREFIX,
            INIT_GIT_CONTAINER_PREFIX,
        ):
            for unique in (True, False):
                name = generate_container_name(prefix, LONG_CONNECTION_NAME, unique)
                assert len(name) <= MAX_CONTAINER_NAME_LENGTH
                assert name.startswith(prefix)

    def test_generate_container_name_keeps_unique_value_when_truncating(self):
        names = {
            generate_container_name(
                INIT_ARTIFACTS_CONTAINER_PREFIX, LONG_CONNECTION_NAME
            )
            for _ in range(100)
        }
        # Truncation must not collapse distinct runs onto the same name.
        assert len(names) == 100

    def test_generate_container_name_is_a_valid_dns_label(self):
        name = generate_container_name(
            INIT_ARTIFACTS_CONTAINER_PREFIX, LONG_CONNECTION_NAME
        )
        assert not name.startswith("-")
        assert not name.endswith("-")
        assert name == name.lower()

    def test_sanitize_container_name_truncates(self):
        name = sanitize_container_name(
            "polyaxon-init-artifacts-" + LONG_CONNECTION_NAME
        )
        assert len(name) <= MAX_CONTAINER_NAME_LENGTH
        assert not name.endswith("-")

    def test_sanitize_container_name_leaves_valid_names_alone(self):
        assert sanitize_container_name("polyaxon_init_Artifacts") == (
            "polyaxon-init-artifacts"
        )
