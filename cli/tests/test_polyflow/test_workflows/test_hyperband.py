import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict

from polyaxon._flow.matrix import V1Hyperband
from polyaxon._flow.optimization import V1Optimization, V1OptimizationMetric
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.workflow_mark
class TestWorkflowV1Hyperbands(BaseTestCase):
    def test_hyperband_config(self):
        config_dict = {
            "kind": "hyperband",
            "maxIterations": 10,
            "eta": 3,
            "resource": {"name": "steps", "type": "int"},
            "resume": False,
            "metric": V1OptimizationMetric(
                name="loss", optimization=V1Optimization.MINIMIZE
            ).to_dict(),
            "params": {"lr": {"kind": "choice", "value": [[0.1], [0.9]]}},
        }
        config = V1Hyperband.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        # Raises for negative values
        config_dict["maxIterations"] = 0
        with self.assertRaises(ValidationError):
            V1Hyperband.from_dict(config_dict)

        config_dict["maxIterations"] = -0.5
        with self.assertRaises(ValidationError):
            V1Hyperband.from_dict(config_dict)

        config_dict["maxIterations"] = 3
        # Add numRuns percent
        config_dict["eta"] = -0.5
        with self.assertRaises(ValidationError):
            V1Hyperband.from_dict(config_dict)

        config_dict["eta"] = 2.9
        config = V1Hyperband.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
