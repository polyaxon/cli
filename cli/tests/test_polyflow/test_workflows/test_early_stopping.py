import pytest

from clipped.utils.assertions import assert_equal_dict

from polyaxon._flow.early_stopping import V1FailureEarlyStopping, V1MetricEarlyStopping
from polyaxon._flow.optimization import V1Optimization
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.workflow_mark
class TestEarlyStoppingConfigs(BaseTestCase):
    def test_metric_early_stopping(self):
        config_dict = {
            "kind": "metric_early_stopping",
            "metric": "loss",
            "value": 0.1,
            "optimization": V1Optimization.MAXIMIZE,
        }
        config = V1MetricEarlyStopping.from_dict(config_dict)
        config_to_dict = config.to_dict()
        assert config_to_dict.pop("optimization") == V1Optimization.MAXIMIZE
        assert_equal_dict(config_to_dict, config_dict)

    def test_metric_early_stopping_with_median_policy(self):
        config_dict = {
            "kind": "metric_early_stopping",
            "metric": "loss",
            "value": 0.1,
            "optimization": V1Optimization.MINIMIZE,
            "policy": {"kind": "median", "evaluationInterval": 1},
        }
        config = V1MetricEarlyStopping.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

    def test_metric_early_stopping_with_average_policy(self):
        config_dict = {
            "kind": "metric_early_stopping",
            "metric": "loss",
            "value": 0.1,
            "optimization": V1Optimization.MINIMIZE,
            "policy": {
                "kind": "diff",
                "evaluationInterval": 1,
                "minSamples": 3,
                "percent": 0.1,
            },
        }
        config = V1MetricEarlyStopping.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

    def test_metric_early_stopping_with_truncation_policy(self):
        config_dict = {
            "kind": "metric_early_stopping",
            "metric": "loss",
            "value": 0.1,
            "optimization": V1Optimization.MAXIMIZE,
            "policy": {"kind": "truncation", "percent": 0.5, "evaluationInterval": 1},
        }
        config = V1MetricEarlyStopping.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

    def test_failure_early_stopping_with_truncation_policy(self):
        config_dict = {
            "kind": "failure_early_stopping",
            "percent": 0.3,
        }
        config = V1FailureEarlyStopping.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
