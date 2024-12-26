import pytest

from clipped.compact.pydantic import PYDANTIC_VERSION, ValidationError
from clipped.utils.assertions import assert_equal_dict

from polyaxon._flow import V1CompiledOperation, V1GridSearch, V1RunKind
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.workflow_mark
class TestWorkflowV1GridSearch(BaseTestCase):
    def test_grid_search_config(self):
        config_dict = {
            "kind": "grid",
            "numRuns": 10,
            "params": {"lr": {"kind": "choice", "value": [[0.1], [0.9]]}},
        }
        config = V1GridSearch.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

        # Raises for negative values
        config_dict["numRuns"] = -5
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        config_dict["numRuns"] = -0.5
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        # Add n_runs percent
        config_dict["numRuns"] = 0.5
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        config_dict["numRuns"] = 5
        config = V1GridSearch.from_dict(config_dict)
        assert_equal_dict(config.to_dict(), config_dict)

    def test_grid_search_without_num_runs(self):
        config_dict = {
            "kind": "compiled_operation",
            "matrix": {
                "kind": "grid",
                "concurrency": 1,
                "params": {"lr": {"kind": "choice", "value": [1, 2, 3]}},
                "earlyStopping": [],
            },
            "run": {"kind": V1RunKind.JOB, "container": {"image": "foo/bar"}},
        }
        config = V1CompiledOperation.from_dict(config_dict)
        assert config.to_dict() == config_dict


@pytest.mark.workflow_mark
class TestWorkflowV1GridSearchBackfill(BaseTestCase):
    def test_date_backfill_config(self):
        config_dict = {
            "kind": "grid",
            "concurrency": 1,
            "numRuns": 10,
            "params": {
                "dates": {
                    "kind": "daterange",
                    "value": {
                        "start": "2019-06-22",
                        "stop": "2019-07-25",
                        "step": 4,
                    },
                }
            },
        }
        config = V1GridSearch.from_dict(config_dict)
        assert_equal_dict(
            config.to_dict(),
            config_dict,
            date_keys=["start", "stop"],
            timedelta_keys=["step"],
        )

        # Raises for negative values
        config_dict["numRuns"] = -5
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        config_dict["numRuns"] = -0.5
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        # Add n_runs percent
        config_dict["numRuns"] = 0.5
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        config_dict["numRuns"] = 5
        config = V1GridSearch.from_dict(config_dict)
        assert_equal_dict(
            config.to_dict(),
            config_dict,
            date_keys=["start", "stop"],
            timedelta_keys=["step"],
        )

    def test_datetime_backfill_config(self):
        config_dict = {
            "kind": "grid",
            "concurrency": 1,
            "numRuns": 10,
            "params": {
                "dates": {
                    "kind": "datetimerange",
                    "value": {
                        "start": "2019-06-22T12:12:00",
                        "stop": "2019-07-25T13:34:00",
                        "step": 4 * 3600,
                    },
                }
            },
        }
        config = V1GridSearch.from_dict(config_dict)
        assert_equal_dict(
            config.to_dict(),
            config_dict,
            datetime_keys=["start", "stop"],
            timedelta_keys=["step"],
        )

        # Raises for negative values
        config_dict["numRuns"] = -5
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        config_dict["numRuns"] = -0.5
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        # Add n_runs percent
        config_dict["numRuns"] = 0.5
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        config_dict["numRuns"] = 5
        config = V1GridSearch.from_dict(config_dict)
        assert_equal_dict(
            config.to_dict(),
            config_dict,
            datetime_keys=["start", "stop"],
            timedelta_keys=["step"],
        )

    def test_wrong_date_backfill_config(self):
        config_dict = {
            "kind": "grid",
            "concurrency": 1,
            "numRuns": 10,
            "params": {
                "dates": {
                    "kind": "daterange",
                    "value": ["2019-07-25", "2019-06-22", 2],
                }
            },
        }
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        config_dict = {
            "kind": "grid",
            "concurrency": 1,
            "numRuns": 10,
            "params": {
                "dates": {
                    "kind": "daterange",
                    "value": ["2019-05-25", "2019-06-22 00:00", 2],
                }
            },
        }
        if PYDANTIC_VERSION.startswith("2."):
            config = V1GridSearch.from_dict(config_dict).to_dict()
            params = config.pop("params")
            expected_params = config_dict.pop("params")
            assert config == config_dict
            assert params["dates"]["kind"] == expected_params["dates"]["kind"]
            assert (
                str(params["dates"]["value"]["start"])
                == expected_params["dates"]["value"][0]
            )
            # the 00:00
            assert (
                str(params["dates"]["value"]["stop"])
                != expected_params["dates"]["value"][1]
            )
            assert (
                params["dates"]["value"]["step"] == expected_params["dates"]["value"][2]
            )
        else:
            with self.assertRaises(ValidationError):
                V1GridSearch.from_dict(config_dict)

    def test_wrong_datetime_backfill_config(self):
        config_dict = {
            "kind": "grid",
            "concurrency": 1,
            "numRuns": 10,
            "params": {
                "dates": {
                    "kind": "datetimerange",
                    "value": ["2019-07-25 00:00", "2019-06-22 00:00", 3600 * 24],
                }
            },
        }
        with self.assertRaises(ValidationError):
            V1GridSearch.from_dict(config_dict)

        config_dict = {
            "kind": "grid",
            "concurrency": 1,
            "numRuns": 10,
            "params": {
                "dates": {
                    "kind": "datetimerange",
                    "value": ["2019-05-25", "2019-06-22 00:00:00", 3600 * 24],
                }
            },
        }
        if PYDANTIC_VERSION.startswith("2."):
            config = V1GridSearch.from_dict(config_dict).to_dict()
            params = config.pop("params")
            expected_params = config_dict.pop("params")
            assert config == config_dict
            assert params["dates"]["kind"] == expected_params["dates"]["kind"]
            # the date is not datetime
            assert (
                str(params["dates"]["value"]["start"])
                != expected_params["dates"]["value"][0]
            )
            assert (
                str(params["dates"]["value"]["stop"])
                == expected_params["dates"]["value"][1]
            )
            assert (
                params["dates"]["value"]["step"].total_seconds()
                == expected_params["dates"]["value"][2]
            )
        else:
            with self.assertRaises(ValidationError):
                V1GridSearch.from_dict(config_dict)
