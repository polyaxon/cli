from polyaxon._deploy.schemas.cache import CacheConfig
from polyaxon._utils.test_utils import BaseTestCase


class TestCacheConfig(BaseTestCase):
    def test_cache_config(self):
        config_dict = {"enabled": True}
        config = CacheConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict

        config_dict = {"enabled": False}
        config = CacheConfig.from_dict(config_dict)
        assert config.to_dict() == config_dict

        config = CacheConfig.from_dict({})
        assert config.to_dict() == {}
        assert config.to_light_dict() == {}
