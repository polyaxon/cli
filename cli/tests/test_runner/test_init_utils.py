import pytest

from polyaxon.auxiliaries import get_init_resources
from polyaxon.k8s import k8s_schemas
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.converter_mark
class TestInitUtils(BaseTestCase):
    def test_get_init_resources(self):
        assert get_init_resources() == k8s_schemas.V1ResourceRequirements(
            limits={"cpu": "1", "memory": "500Mi"},
            requests={"cpu": "0.1", "memory": "60Mi"},
        )
