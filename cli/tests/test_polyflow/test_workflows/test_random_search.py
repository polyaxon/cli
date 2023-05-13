import pytest

from clipped.utils.assertions import assert_equal_dict
from pydantic import ValidationError

from polyaxon.polyflow import V1RunKind
from polyaxon.polyflow.matrix.random_search import V1RandomSearch
from polyaxon.polyflow.operations import V1CompiledOperation
from polyaxon.utils.test_utils import BaseTestCase


@pytest.mark.workflow_mark
class TestWorkflowV1RandomSearch(BaseTestCase):
    def test_random_search_config(self):
        config_dict = {
            "kind": "random",
            "numRuns": 10,
            "params": {"lr": {"kind": "choice", "value": [[0.1], [0.9]]}},
        }
        config = V1RandomSearch.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        # Raises for negative values
        config_dict["numRuns"] = -5
        with self.assertRaises(ValidationError):
            V1RandomSearch.from_dict(config_dict)

        config_dict["numRuns"] = -0.5
        with self.assertRaises(ValidationError):
            V1RandomSearch.from_dict(config_dict)

        # Add n_runs percent
        config_dict["numRuns"] = 0.5
        with self.assertRaises(ValidationError):
            V1RandomSearch.from_dict(config_dict)

        config_dict["numRuns"] = 5
        config = V1RandomSearch.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

    def test_random_search_without_num_runs(self):
        config_dict = {
            "kind": "compiled_operation",
            "matrix": {
                "kind": "random",
                "concurrency": 1,
                "params": {"lr": {"kind": "choice", "value": [1, 2, 3]}},
                "seed": 1,
                "earlyStopping": [],
            },
            "run": {"kind": V1RunKind.JOB, "container": {"image": "test"}},
        }
        with self.assertRaises(ValidationError):
            V1CompiledOperation.from_dict(config_dict)

        config_dict["matrix"]["numRuns"] = 10
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_dict() == config_dict
