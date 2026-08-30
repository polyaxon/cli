import pytest

from clipped.compact.pydantic import ValidationError
from clipped.utils.assertions import assert_equal_dict
from polyaxon._flow.joins import V1Join
from polyaxon._flow.matrix.tpe import V1TPE
from polyaxon._flow.operations import V1CompiledOperation
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._operations import get_tpe_tuner
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.workflow_mark
class TestWorkflowV1TPE(BaseTestCase):
    def test_tpe_config(self):
        config_dict = {
            "kind": "tpe",
            "numRuns": 10,
            "metric": {"name": "loss", "optimization": "minimize"},
            "params": {"lr": {"kind": "choice", "value": [0.1, 0.9]}},
        }

        config = V1TPE.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        for algorithm in ("tpe", "rand", "anneal"):
            config_dict["algorithm"] = algorithm
            with self.assertRaises(ValidationError):
                V1TPE.from_dict(config_dict)

    def test_removed_matrix_kind_is_rejected(self):
        matrix = {
            "kind": "hyperopt",
            "numRuns": 10,
            "metric": {"name": "loss", "optimization": "minimize"},
            "params": {"lr": {"kind": "choice", "value": [0.1, 0.9]}},
        }

        with self.assertRaises(ValidationError):
            V1TPE.from_dict(matrix)

        with self.assertRaises(ValidationError):
            V1CompiledOperation.from_dict(
                {
                    "kind": "compiled_operation",
                    "matrix": matrix,
                    "run": {
                        "kind": V1RunKind.JOB,
                        "container": {"image": "test"},
                    },
                }
            )

    def test_tpe_tuner_operation(self):
        matrix = V1TPE.from_dict(
            {
                "kind": "tpe",
                "numRuns": 10,
                "metric": {"name": "loss", "optimization": "minimize"},
                "params": {"lr": {"kind": "choice", "value": [0.1, 0.9]}},
            }
        )

        operation = get_tpe_tuner(
            matrix=matrix,
            join=V1Join(query="metrics.loss:<1"),
            iteration=1,
        )

        assert operation.hub_ref == "tpe-tuner"
        assert_equal_dict(operation.params["matrix"].value, matrix.to_light_dict())
