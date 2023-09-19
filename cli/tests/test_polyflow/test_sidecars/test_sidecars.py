import pytest

from polyaxon.polyflow import V1CompiledOperation, V1RunKind
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.sidecars_mark
class TestSidecars(BaseTestCase):
    def test_sidecars_config(self):
        config_dict = {
            "kind": "compiled_operation",
            "run": {
                "kind": V1RunKind.JOB,
                "container": {"image": "foo/bar"},
                "sidecars": [
                    {"name": "sidecar1", "args": ["/subpath1", "subpath2"]},
                    {"name": "sidecar2", "args": ["/subpath1", "subpath2"]},
                ],
            },
        }
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_light_dict() == config_dict
