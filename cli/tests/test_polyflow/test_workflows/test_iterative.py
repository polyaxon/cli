import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict

from polyaxon.polyflow.matrix.iterative import V1Iterative
from polyaxon.polyflow.operations import V1CompiledOperation
from polyaxon.polyflow.run.enums import V1RunKind
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.workflow_mark
class TestWorkflowV1Iterative(BaseTestCase):
    def test_iterative_config(self):
        config_dict = {
            "kind": "iterative",
            "maxIterations": 10,
            "tuner": {"hubRef": "org/my-matrix-tuner"},
        }
        config = V1Iterative.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        # Raises for negative values
        config_dict["maxIterations"] = -5
        with self.assertRaises(ValidationError):
            V1Iterative.from_dict(config_dict)

        config_dict["maxIterations"] = -0.5
        with self.assertRaises(ValidationError):
            V1Iterative.from_dict(config_dict)

        # Add num_runs percent
        config_dict["maxIterations"] = 0.5
        with self.assertRaises(ValidationError):
            V1Iterative.from_dict(config_dict)

        config_dict["maxIterations"] = 5
        config = V1Iterative.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

    def test_iterative_without_max_iterations(self):
        config_dict = {
            "kind": "compiled_operation",
            "matrix": {
                "kind": "iterative",
                "params": {"lr": {"kind": "choice", "value": [1, 2, 3]}},
                "seed": 1,
                "tuner": {"hubRef": "org/my-matrix-tuner"},
            },
            "run": {"kind": V1RunKind.JOB, "container": {"image": "foo/bar"}},
        }

        with self.assertRaises(ValidationError):
            V1CompiledOperation.from_dict(config_dict)

        config_dict["matrix"]["maxIterations"] = 10
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_dict() == config_dict
