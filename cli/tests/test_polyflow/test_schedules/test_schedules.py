import pytest

from typing import List

from clipped.compact.pydantic import ValidationError
from clipped.utils.json import orjson_dumps
from clipped.utils.tz import now

from polyaxon._flow.schedules import (
    V1CronSchedule,
    V1DateTimeSchedule,
    V1IntervalSchedule,
    V1Schedule,
)
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon._utils.test_utils import BaseTestCase


@pytest.mark.polyflow_mark
class TestScheduleConfigs(BaseTestCase):
    def test_interval_schedule(self):
        config_dict = {"frequency": 2, "startAt": "foo"}
        with self.assertRaises(ValidationError):
            V1IntervalSchedule.from_dict(config_dict)

        config_dict = {"frequency": "foo", "startAt": now().isoformat()}
        with self.assertRaises(ValidationError):
            V1IntervalSchedule.from_dict(config_dict)

        config_dict = {
            "kind": "cron",
            "startAt": now().isoformat(),
            "endAt": now().isoformat(),
            "frequency": 2.0,
        }
        with self.assertRaises(ValidationError):
            V1IntervalSchedule.from_dict(config_dict)

        config_dict = {
            "kind": "interval",
            "startAt": now().isoformat(),
            "frequency": 2.0,
        }
        assert V1IntervalSchedule.from_dict(config_dict).to_json() == orjson_dumps(
            config_dict
        )

        config_dict = {
            "kind": "interval",
            "startAt": now().isoformat(),
            "endAt": now().isoformat(),
            "frequency": 2.0,
        }
        assert V1IntervalSchedule.from_dict(config_dict).to_json() == orjson_dumps(
            config_dict
        )

        config_dict = {
            "kind": "interval",
            "startAt": now().isoformat(),
            "endAt": now().isoformat(),
            "maxRuns": 123,
            "frequency": 2.0,
            "dependsOnPast": False,
        }
        assert V1IntervalSchedule.from_dict(config_dict).to_json() == orjson_dumps(
            config_dict
        )

    def test_cron_schedule(self):
        config_dict = {"cron": 2, "startAt": "foo"}
        with self.assertRaises(ValidationError):
            V1CronSchedule.from_dict(config_dict)

        config_dict = {
            "kind": "interval",
            "cron": "0 0 * * *",
            "startAt": now().isoformat(),
            "endAt": now().isoformat(),
        }
        with self.assertRaises(ValidationError):
            V1CronSchedule.from_dict(config_dict)

        config_dict = {"kind": "cron", "cron": "0 0 * * *"}
        assert V1CronSchedule.from_dict(config_dict).to_json() == orjson_dumps(
            config_dict
        )

        config_dict = {
            "kind": "cron",
            "cron": "0 0 * * *",
            "startAt": now().isoformat(),
            "endAt": now().isoformat(),
        }
        assert V1CronSchedule.from_dict(config_dict).to_json() == orjson_dumps(
            config_dict
        )

        config_dict = {
            "kind": "cron",
            "cron": "0 0 * * *",
            "startAt": now().isoformat(),
            "endAt": now().isoformat(),
            "maxRuns": 123,
            "dependsOnPast": False,
        }
        assert V1CronSchedule.from_dict(config_dict).to_json() == orjson_dumps(
            config_dict
        )

    def test_date_schedule(self):
        config_dict = {"startAt": "foo"}
        with self.assertRaises(ValidationError):
            V1DateTimeSchedule.from_dict(config_dict)

        config_dict = {"kind": "datetime", "startAt": now().isoformat()}
        assert V1DateTimeSchedule.from_dict(config_dict).to_json() == orjson_dumps(
            config_dict
        )

    def test_schedule(self):
        configs = [
            {
                "kind": "interval",
                "startAt": now().isoformat(),
                "endAt": now().isoformat(),
                "frequency": 2.0,
                "dependsOnPast": False,
            },
            {
                "kind": "cron",
                "cron": "0 0 * * *",
                "startAt": now().isoformat(),
                "endAt": now().isoformat(),
                "dependsOnPast": True,
            },
            {
                "kind": "datetime",
                "startAt": now().isoformat(),
            },
        ]

        class DummyModel(BaseSchemaModel):
            schedules: List[V1Schedule]

        result = DummyModel(schedules=configs)

        assert result.to_json() == orjson_dumps({"schedules": configs})
