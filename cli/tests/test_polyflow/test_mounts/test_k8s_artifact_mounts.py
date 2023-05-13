import pytest

from clipped.utils.assertions import assert_equal_dict
from pydantic import ValidationError

from polyaxon.polyflow.mounts import V1ArtifactsMount
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.mounts_mark
class TestArtifactConfigs(BaseTestCase):
    def test_artifact_config(self):
        config_dict = {"name": "foo"}
        config = V1ArtifactsMount.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        config_dict = {"name": "foo", "managed": 213}
        with self.assertRaises(ValidationError):
            V1ArtifactsMount.from_dict(config_dict)

        config_dict = {"name": "foo", "paths": ["item1", "item2"]}
        config = V1ArtifactsMount.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        config_dict = {"name": "foo", "paths": ["item1", "item2"]}
        config = V1ArtifactsMount.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
