import os
import pytest
import re
import tempfile
from unittest import mock
from uuid import UUID

from polyaxon._containers.names import generate_container_name
from polyaxon._contexts import paths as ctx_paths
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.container_mark
class TestContainerNames(BaseTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        patcher = mock.patch.object(
            ctx_paths,
            "CONTEXT_USER_POLYAXON_PATH",
            os.path.join(directory.name, ".polyaxon"),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()
        self.uuid4_patch = mock.patch(
            "uuid.uuid4", return_value=UUID("0123456789abcdef0123456789abcdef")
        )
        self.uuid4 = self.uuid4_patch.start()
        self.addCleanup(self.uuid4_patch.stop)

    def test_generated_name_without_unique_suffix(self):
        assert (
            generate_container_name("polyaxon-init-artifacts", "default", False)
            == "polyaxon-init-artifacts-default"
        )

    def test_generated_name_with_unique_suffix(self):
        assert generate_container_name("init", "name", True) == "init-name-0123456789"

    def test_generated_name_preserves_separator(self):
        assert generate_container_name("init-", "name", True) == "init--name-0123456789"

    def test_generated_name_preserves_separator_without_suffix(self):
        assert generate_container_name("init-", None, True) == "init--0123456789"

    def test_generated_name_normalizes_repeated_underscores(self):
        assert (
            generate_container_name("init", "repo__name", True)
            == "init-repo-name-0123456789"
        )

    def test_generated_name_normalizes_case_and_invalid_characters(self):
        assert (
            generate_container_name("INIT", "Repo/Branch.É", True)
            == "init-repo-branch-0123456789"
        )

    def test_generated_name_with_only_invalid_characters(self):
        assert generate_container_name("---", ".../", True) == "container-0123456789"

    def test_deterministic_name_with_only_invalid_characters(self):
        assert generate_container_name("---", ".../", False) == "container"

    def test_generated_name_with_missing_prefix_and_suffix(self):
        assert generate_container_name(None, None, False) == "container-0123456789"

    def test_generated_name_with_empty_prefix_and_suffix(self):
        assert generate_container_name("", "", False) == "container-0123456789"

    def test_generated_name_with_numeric_prefix_and_suffix(self):
        assert generate_container_name("123", "456", False) == "123-456"

    def test_generated_name_length_boundary(self):
        for connection_length, expected_length in (
            (27, 62),
            (28, 63),
            (29, 63),
            (200, 63),
        ):
            with self.subTest(connection_length=connection_length):
                name = generate_container_name(
                    "polyaxon-init-artifacts", "a" * connection_length
                )

                assert len(name) == expected_length
                assert name.startswith("polyaxon-init-artifacts-")
                assert name.endswith("-0123456789")
                assert re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", name)

    def test_generated_name_with_long_prefix(self):
        assert generate_container_name("a" * 100, "store") == ("a" * 52 + "-0123456789")

    def test_truncation_removes_trailing_separator(self):
        assert generate_container_name("a" * 51, "store") == ("a" * 51 + "-0123456789")

    def test_truncation_preserves_distinct_uuid_suffixes(self):
        self.uuid4.side_effect = [
            UUID("0123456789abcdef0123456789abcdef"),
            UUID("fedcba9876543210fedcba9876543210"),
        ]
        first = generate_container_name("polyaxon-init-artifacts", "a" * 100)
        second = generate_container_name("polyaxon-init-artifacts", "a" * 100)

        assert first != second
        assert len(first) == len(second) == 63
        assert first.endswith("-0123456789")
        assert second.endswith("-fedcba9876")

    def test_deterministic_name_within_length_limit(self):
        self.uuid4_patch.stop()
        for suffix_length in (57, 58):
            with self.subTest(suffix_length=suffix_length):
                suffix = "a" * suffix_length
                name = generate_container_name("init", suffix, unique=False)

                assert name == generate_container_name("init", suffix, unique=False)
                assert len(name) == 5 + suffix_length
                assert re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", name)
                assert name == "init-" + suffix

    def test_deterministic_name_with_truncation(self):
        self.uuid4_patch.stop()
        for suffix_length in (59, 200):
            with self.subTest(suffix_length=suffix_length):
                suffix = "a" * suffix_length
                name = generate_container_name("init", suffix, unique=False)

                assert name == generate_container_name("init", suffix, unique=False)
                assert len(name) == 63
                assert re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", name)

    def test_deterministic_truncation_uses_the_complete_original_name(self):
        self.uuid4_patch.stop()
        prefix = "a" * 100
        first = generate_container_name(prefix, "Store_A", unique=False)
        second = generate_container_name(prefix, "store-a", unique=False)

        assert first == generate_container_name(prefix, "Store_A", unique=False)
        assert first != second
        assert first[:53] == second[:53] == "a" * 52 + "-"
        assert len(first) == len(second) == 63
        assert re.fullmatch(r"[0-9a-f]{10}", first[53:])
        assert re.fullmatch(r"[0-9a-f]{10}", second[53:])
