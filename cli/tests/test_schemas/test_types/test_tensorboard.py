import pytest

from polyaxon._schemas.types.tensorboard import V1TensorboardType
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.init_mark
class TestTensorboardInitConfigs(BaseTestCase):
    def test_tb_type(self):
        config_dict = {
            "port": 6006,
            "uuids": [
                "d1410a914d18457589b91926d8c23db4",
                "56f1a7f20f1d4f7f9e1a108b3c6b6031",
            ],
            "useNames": True,
            "plugins": ["tensorboard-plugin-profile"],
        }
        config = V1TensorboardType.from_dict(config_dict)
        assert config.to_dict() == config_dict
