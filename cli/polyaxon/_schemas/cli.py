from typing import Optional

from clipped.compact.pydantic import StrictStr

from polyaxon import _dist
from polyaxon._schemas.checks import ChecksConfig
from polyaxon._schemas.compatibility import V1Compatibility
from polyaxon._schemas.installation import V1Installation
from polyaxon._schemas.log_handler import V1LogHandler


class CliConfig(ChecksConfig):
    _IDENTIFIER = "cli"
    _DIST = "dist"
    _INTERVAL = 30 * 60

    current_version: Optional[StrictStr]
    installation: Optional[V1Installation]
    compatibility: Optional[V1Compatibility]
    log_handler: Optional[V1LogHandler]

    @property
    def min_version(self) -> Optional[str]:
        if not self.compatibility or not self.compatibility.cli:
            return None
        return self.compatibility.cli.min

    @property
    def latest_version(self) -> Optional[str]:
        if not self.compatibility or not self.compatibility.cli:
            return None
        return self.compatibility.cli.latest

    @property
    def is_community(self) -> bool:
        return self.installation is None or _dist.is_community(self.installation.dist)
