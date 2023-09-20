from clipped.compact.pydantic import ValidationError

from polyaxon._deploy.schemas.celery import CeleryConfig
from polyaxon._utils.test_utils import BaseTestCase


class TestCeleryConfig(BaseTestCase):
    def test_celery_config(self):
        config_dict = {
            "confirmPublish": 12,
            "workerPrefetchMultiplier": "foo",
            "workerMaxTasksPerChild": 123,
            "workerMaxMemoryPerChild": 123,
        }
        with self.assertRaises(ValidationError):
            CeleryConfig.from_dict(config_dict)

        config_dict = {
            "taskTrackStarted": True,
            "brokerPoolLimit": 123,
            "confirmPublish": True,
            "workerPrefetchMultiplier": 4,
            "workerMaxTasksPerChild": 123,
            "workerMaxMemoryPerChild": 123,
        }
        config = CeleryConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict

        config_dict = {"confirmPublish": True, "workerMaxMemoryPerChild": 123}
        config = CeleryConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict
