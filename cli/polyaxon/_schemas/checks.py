import os

from datetime import datetime, timedelta
from typing import Optional

from clipped.utils.tz import now

from polyaxon._env_vars.keys import ENV_KEYS_INTERVALS_COMPATIBILITY_CHECK
from polyaxon._schemas.base import BaseSchemaModel


class ChecksConfig(BaseSchemaModel):
    _IDENTIFIER = "checks"
    _INTERVAL = 30 * 60

    last_check: Optional[datetime]

    def __init__(
        self,
        last_check=None,
        **data,
    ):
        last_check = self.get_last_check(last_check)
        super().__init__(last_check=last_check, **data)

    def get_interval(self, interval: Optional[int] = None) -> int:
        if interval is not None:
            return interval
        interval = int(
            os.environ.get(ENV_KEYS_INTERVALS_COMPATIBILITY_CHECK, self._INTERVAL)
        )
        if interval == -1:
            return interval
        return max(interval, self._INTERVAL)

    @classmethod
    def get_last_check(cls, last_check) -> datetime:
        return last_check or now() - timedelta(cls._INTERVAL)

    def should_check(self, interval: Optional[int] = None) -> bool:
        interval = self.get_interval(interval=interval)
        if interval == -1:
            return False
        if (now() - self.last_check).total_seconds() > interval:
            return True
        return False
