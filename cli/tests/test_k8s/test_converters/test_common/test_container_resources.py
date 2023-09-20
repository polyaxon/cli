import pytest

from polyaxon._k8s.converter.base.containers import ContainerMixin
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.k8s_mark
class TestResourceRequirements(BaseTestCase):
    def test_empty_sanitize_resources(self):
        resources = ContainerMixin._sanitize_resources(None)
        assert resources is None

    def test_empty_dict_sanitize_resources(self):
        resources = ContainerMixin._sanitize_resources({})
        assert resources is None

    def test_sanitize_resources_containing_ints(self):
        resources = ContainerMixin._sanitize_resources(
            {"requests": {"cpu": 1, "memory": "100Mi", "nvidia.com/gpu": 1}}
        )
        assert resources.limits is None
        assert resources.requests == {
            "cpu": "1",
            "memory": "100Mi",
            "nvidia.com/gpu": "1",
        }

        resources = ContainerMixin._sanitize_resources(
            {"limits": {"cpu": "1", "memory": "100Mi", "nvidia.com/gpu": "1"}}
        )
        assert resources.limits == {
            "cpu": "1",
            "memory": "100Mi",
            "nvidia.com/gpu": "1",
        }
        assert resources.requests is None

        resources = ContainerMixin._sanitize_resources(
            {
                "requests": {"cpu": "1", "memory": "100Mi", "nvidia.com/gpu": "1"},
                "limits": {"cpu": "1", "memory": "100Mi", "nvidia.com/gpu": "1"},
            }
        )
        assert resources.limits == {
            "cpu": "1",
            "memory": "100Mi",
            "nvidia.com/gpu": "1",
        }
        assert resources.requests == {
            "cpu": "1",
            "memory": "100Mi",
            "nvidia.com/gpu": "1",
        }
