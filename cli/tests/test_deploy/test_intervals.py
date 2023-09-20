from clipped.compact.pydantic import ValidationError

from polyaxon._deploy.schemas.intervals import IntervalsConfig
from polyaxon._utils.test_utils import BaseTestCase


class TestIntervalsConfig(BaseTestCase):
    def test_intervals_config(self):
        bad_config_dicts = [
            {"runsScheduler": "dsf"},
            {"operationsDefaultRetryDelay": "dsf"},
            {"operationsMaxRetryDelay": ["dsf"]},
        ]

        for config_dict in bad_config_dicts:
            with self.assertRaises(ValidationError):
                IntervalsConfig.from_dict(config_dict)

        config_dict = {
            "runsScheduler": 12,
            "operationsDefaultRetryDelay": 12,
            "operationsMaxRetryDelay": 12,
        }
        config = IntervalsConfig.from_dict(config_dict)
        assert config.to_light_dict() == config_dict
