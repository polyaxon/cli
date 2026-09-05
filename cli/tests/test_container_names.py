import pytest
import re
from unittest import mock
from uuid import UUID

from polyaxon._containers.names import generate_container_name


pytestmark = pytest.mark.container_mark


@pytest.fixture
def fixed_uuid():
    with mock.patch(
        "uuid.uuid4", return_value=UUID("0123456789abcdef0123456789abcdef")
    ):
        yield


@pytest.mark.parametrize(
    "prefix,suffix,unique,expected",
    [
        (
            "polyaxon-init-artifacts",
            "default",
            False,
            "polyaxon-init-artifacts-default",
        ),
        ("init", "name", True, "init-name-0123456789"),
        ("init-", "name", True, "init--name-0123456789"),
        ("init-", None, True, "init--0123456789"),
        ("init", "repo__name", True, "init-repo-name-0123456789"),
        ("INIT", "Repo/Branch.É", True, "init-repo-branch-0123456789"),
        ("---", ".../", True, "container-0123456789"),
        ("---", ".../", False, "container"),
        (None, None, False, "container-0123456789"),
        ("", "", False, "container-0123456789"),
        ("123", "456", False, "123-456"),
    ],
)
def test_generated_container_name(fixed_uuid, prefix, suffix, unique, expected):
    assert generate_container_name(prefix, suffix, unique) == expected


@pytest.mark.parametrize(
    "connection_length,expected_length",
    [(27, 62), (28, 63), (29, 63), (200, 63)],
)
def test_generated_name_length_boundary(fixed_uuid, connection_length, expected_length):
    name = generate_container_name("polyaxon-init-artifacts", "a" * connection_length)

    assert len(name) == expected_length
    assert name.startswith("polyaxon-init-artifacts-")
    assert name.endswith("-0123456789")
    assert re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", name)


def test_generated_name_with_long_prefix(fixed_uuid):
    assert generate_container_name("a" * 100, "store") == ("a" * 52 + "-0123456789")


def test_truncation_removes_trailing_separator(fixed_uuid):
    assert generate_container_name("a" * 51, "store") == ("a" * 51 + "-0123456789")


def test_truncation_preserves_distinct_uuid_suffixes():
    with mock.patch(
        "uuid.uuid4",
        side_effect=[
            UUID("0123456789abcdef0123456789abcdef"),
            UUID("fedcba9876543210fedcba9876543210"),
        ],
    ):
        first = generate_container_name("polyaxon-init-artifacts", "a" * 100)
        second = generate_container_name("polyaxon-init-artifacts", "a" * 100)

    assert first != second
    assert len(first) == len(second) == 63
    assert first.endswith("-0123456789")
    assert second.endswith("-fedcba9876")


@pytest.mark.parametrize("suffix_length", [57, 58, 59, 200])
def test_deterministic_name_length_boundary(suffix_length):
    suffix = "a" * suffix_length
    name = generate_container_name("init", suffix, unique=False)

    assert name == generate_container_name("init", suffix, unique=False)
    assert len(name) == min(5 + suffix_length, 63)
    assert re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", name)
    if suffix_length <= 58:
        assert name == "init-" + suffix


def test_deterministic_truncation_uses_the_complete_original_name():
    prefix = "a" * 100
    first = generate_container_name(prefix, "Store_A", unique=False)
    second = generate_container_name(prefix, "store-a", unique=False)

    assert first == generate_container_name(prefix, "Store_A", unique=False)
    assert first != second
    assert first[:53] == second[:53] == "a" * 52 + "-"
    assert len(first) == len(second) == 63
    assert re.fullmatch(r"[0-9a-f]{10}", first[53:])
    assert re.fullmatch(r"[0-9a-f]{10}", second[53:])
