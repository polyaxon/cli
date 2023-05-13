import pytest

from clipped.utils.assertions import assert_equal_dict
from pydantic import ValidationError

from polyaxon.polyflow.matrix.bayes import (
    AcquisitionFunctions,
    GaussianProcessConfig,
    GaussianProcessesKernels,
    UtilityFunctionConfig,
    V1Bayes,
)
from polyaxon.polyflow.optimization import V1Optimization, V1OptimizationMetric
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.workflow_mark
class TestWorkflowV1Bayes(BaseTestCase):
    def test_gaussian_process_config(self):
        config_dict = {
            "kernel": GaussianProcessesKernels.MATERN,
            "lengthScale": 1.0,
            "nu": 1.9,
            "numRestartsOptimizer": 2,
        }
        config = GaussianProcessConfig.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

    def test_utility_function_config(self):
        config_dict = {"acquisitionFunction": AcquisitionFunctions.UCB}
        with self.assertRaises(ValidationError):
            UtilityFunctionConfig.from_dict(config_dict)

        config_dict = {"acquisitionFunction": AcquisitionFunctions.POI}
        with self.assertRaises(ValidationError):
            UtilityFunctionConfig.from_dict(config_dict)

        config_dict = {
            "acquisitionFunction": AcquisitionFunctions.UCB,
            "kappa": 1.2,
            "gaussianProcess": {
                "kernel": GaussianProcessesKernels.MATERN,
                "lengthScale": 1.0,
                "nu": 1.9,
                "numRestartsOptimizer": 2,
            },
        }
        config = UtilityFunctionConfig.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        config_dict = {
            "acquisitionFunction": AcquisitionFunctions.EI,
            "eps": 1.2,
            "gaussianProcess": {
                "kernel": GaussianProcessesKernels.MATERN,
                "lengthScale": 1.0,
                "nu": 1.9,
                "numRestartsOptimizer": 2,
            },
        }
        config = UtilityFunctionConfig.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

    def test_bayes_config(self):
        config_dict = {
            "kind": "bayes",
            "metric": V1OptimizationMetric(
                name="loss", optimization=V1Optimization.MINIMIZE
            ).to_dict(),
            "numInitialRuns": 2,
            "maxIterations": 19,
            "utilityFunction": {
                "acquisitionFunction": AcquisitionFunctions.UCB,
                "kappa": 1.2,
                "gaussianProcess": {
                    "kernel": GaussianProcessesKernels.MATERN,
                    "lengthScale": 1.0,
                    "nu": 1.9,
                    "numRestartsOptimizer": 2,
                },
            },
            "params": {"lr": {"kind": "choice", "value": [[0.1], [0.9]]}},
        }
        config = V1Bayes.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
