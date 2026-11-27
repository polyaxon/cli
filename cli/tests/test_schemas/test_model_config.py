import pytest

from polyaxon._deploy.schemas.ingress import IngressConfig
from polyaxon._deploy.schemas.service import BaseService, ThirdPartyService
from polyaxon._fs.watcher import FSWatcher, PathData
from polyaxon._schemas.agent import BaseAgentConfig
from polyaxon._schemas.authentication import AccessTokenConfig
from polyaxon._schemas.client import ClientConfig
from polyaxon._schemas.home import HomeConfig
from polyaxon._utils.test_utils import BaseTestCase


BASE_MODEL_CONFIG = {
    "populate_by_name": True,
    "validate_assignment": True,
    "arbitrary_types_allowed": True,
    "use_enum_values": True,
    "ser_json_timedelta": "float",
    "protected_namespaces": (),
}


@pytest.mark.schemas_mark
class TestModelConfig(BaseTestCase):
    def test_schema_model_config(self):
        for cls, overrides in (
            (FSWatcher, {"extra": "forbid", "validate_assignment": False}),
            (BaseService, {"extra": "allow"}),
            (ThirdPartyService, {"extra": "allow"}),
            (IngressConfig, {"extra": "ignore"}),
            (HomeConfig, {"extra": "ignore"}),
            (ClientConfig, {"extra": "ignore"}),
            (AccessTokenConfig, {"extra": "ignore"}),
            (BaseAgentConfig, {"extra": "ignore"}),
        ):
            with self.subTest(cls=cls.__name__):
                expected = {**BASE_MODEL_CONFIG, **overrides}
                assert {k: cls.model_config.get(k) for k in expected} == expected
                assert "Config" not in vars(cls)

    def test_path_data_config(self):
        # PathData is a RootModel, which only sets validate_assignment.
        expected = {k: None for k in BASE_MODEL_CONFIG}
        expected["validate_assignment"] = False
        assert {k: PathData.model_config.get(k) for k in expected} == expected
        assert "Config" not in vars(PathData)
