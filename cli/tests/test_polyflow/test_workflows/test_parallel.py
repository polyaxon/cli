import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict

from polyaxon._flow import (
    AcquisitionFunctions,
    GaussianProcessesKernels,
    V1CompiledOperation,
    V1MatrixKind,
    V1Optimization,
    V1OptimizationMetric,
    V1RunKind,
)
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.workflow_mark
class TestWorkflowConfigs(BaseTestCase):
    def test_workflow_config_raise_conditions(self):
        config_dict = {
            "kind": "compiled_operation",
            "matrix": {
                "kind": "mapping",
                "concurrency": 2,
                "values": [{"foo": 1}, {"foo": 2}, {"foo": 3}],
            },
            "run": {"kind": V1RunKind.JOB, "container": {"image": "test"}},
        }
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_dict() == config_dict

        # Add random_search without matrix should raise
        config_dict["matrix"] = {"kind": "random", "numRuns": 10}
        with self.assertRaises(ValidationError):
            V1CompiledOperation.from_dict(config_dict)

        # Add a matrix definition with 2 methods
        config_dict["matrix"]["params"] = {
            "lr": {
                "kind": "choice",
                "value": [1, 2, 3],
                "pvalues": [(1, 0.3), (2, 0.3), (3, 0.3)],
            }
        }
        with self.assertRaises(ValidationError):
            V1CompiledOperation.from_dict(config_dict)

        # Using a distribution with random search should pass
        config_dict["matrix"]["params"] = {
            "lr": {"kind": "pchoice", "value": [(1, 0.3), (2, 0.3), (3, 0.3)]}
        }
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_dict() == config_dict

        # Add matrix definition should pass
        config_dict["matrix"]["params"] = {"lr": {"kind": "choice", "value": [1, 2, 3]}}
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_dict() == config_dict

        # Add grid_search should raise
        config_dict["matrix"] = {"kind": V1MatrixKind.GRID, "numRuns": 10}
        config_dict["matrix"]["params"] = {"lr": {"kind": "choice", "value": [1, 2, 3]}}
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_dict() == config_dict

        # Adding a distribution should raise
        config_dict["matrix"]["params"] = {
            "lr": {"kind": "pchoice", "value": [(1, 0.3), (2, 0.3), (3, 0.3)]}
        }
        with self.assertRaises(ValidationError):
            V1CompiledOperation.from_dict(config_dict)

        # Updating the matrix should pass
        config_dict["matrix"]["params"] = {"lr": {"kind": "choice", "value": [1, 2, 3]}}
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_dict() == config_dict

        # Add hyperband should raise
        config_dict["matrix"] = {
            "kind": V1MatrixKind.HYPERBAND,
            "maxIterations": 10,
            "eta": 3,
            "resource": {"name": "steps", "type": "int"},
            "resume": False,
            "metric": V1OptimizationMetric(
                name="loss", optimization=V1Optimization.MINIMIZE
            ).to_dict(),
            "params": {
                "lr": {"kind": "pchoice", "value": [(1, 0.3), (2, 0.3), (3, 0.3)]}
            },
            "seed": 1,
        }
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_dict() == config_dict

        # Add early stopping
        config_dict["matrix"]["earlyStopping"] = [
            {
                "kind": "metric_early_stopping",
                "metric": "loss",
                "value": 0.1,
                "optimization": V1Optimization.MINIMIZE,
                "policy": {"kind": "median", "evaluationInterval": 1},
            },
            {
                "kind": "metric_early_stopping",
                "metric": "accuracy",
                "value": 0.9,
                "optimization": V1Optimization.MAXIMIZE,
                "policy": {
                    "kind": "truncation",
                    "percent": 50,
                    "evaluationInterval": 1,
                },
            },
        ]
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_dict() == config_dict

        # Add bayes should raise
        config_dict["matrix"] = {
            "kind": V1MatrixKind.BAYES,
            "metric": V1OptimizationMetric(
                name="loss", optimization=V1Optimization.MINIMIZE
            ).to_dict(),
            "numInitialRuns": 2,
            "maxIterations": 10,
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
            "params": {
                "lr": {"kind": "pchoice", "value": [(1, 0.3), (2, 0.3), (3, 0.3)]}
            },
            "seed": 1,
        }
        with self.assertRaises(ValidationError):
            V1CompiledOperation.from_dict(config_dict)

        # Using non uniform distribution should raise
        # Updating the matrix should pass
        config_dict["matrix"]["params"] = {
            "lr": {"kind": "pchoice", "value": [[0.1, 0.1], [0.2, 0.9]]}
        }
        with self.assertRaises(ValidationError):
            V1CompiledOperation.from_dict(config_dict)

        config_dict["matrix"]["params"] = {
            "lr": {"kind": "normal", "value": [0.1, 0.2]}
        }
        with self.assertRaises(ValidationError):
            V1CompiledOperation.from_dict(config_dict)

        # Using uniform distribution should not raise
        config_dict["matrix"]["params"] = {
            "lr": {"kind": "uniform", "value": {"low": 0.1, "high": 0.2}}
        }
        config = V1CompiledOperation.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)
