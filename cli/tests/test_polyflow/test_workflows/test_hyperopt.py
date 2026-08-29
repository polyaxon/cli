import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict
from polyaxon._flow.matrix.hyperopt import V1Hyperopt
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.workflow_mark
class TestWorkflowV1Hyperopt(BaseTestCase):
    def test_hyperopt_algorithms(self):
        config_dict = {
            "kind": "hyperopt",
            "algorithm": "tpe",
            "numRuns": 10,
            "metric": {"name": "loss", "optimization": "minimize"},
            "params": {"lr": {"kind": "choice", "value": [0.1, 0.9]}},
        }

        config = V1Hyperopt.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        config_dict["algorithm"] = "anneal"
        config = V1Hyperopt.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        config_dict["algorithm"] = "rand"
        with self.assertRaises(ValidationError):
            V1Hyperopt.from_dict(config_dict)
