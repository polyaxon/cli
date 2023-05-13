from polyaxon.deploy.schemas.rbac import RBACConfig
from polyaxon.utils.test_utils import BaseTestCase


class TestRBACConfig(BaseTestCase):
    def test_rbac_config(self):
        config_dict = {"enabled": True}
        config = RBACConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict

        config_dict = {"enabled": False}
        config = RBACConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict

        config = RBACConfig.from_dict({})
        assert config.to_dict() == {}
        assert config.to_light_dict() == {}
