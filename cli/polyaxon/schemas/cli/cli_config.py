from typing import Optional

from pydantic import StrictStr

from polyaxon import dist
from polyaxon.schemas.api.compatibility import V1Compatibility
from polyaxon.schemas.api.installation import V1Installation
from polyaxon.schemas.api.log_handler import V1LogHandler
from polyaxon.schemas.cli.checks_config import ChecksConfig


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
        return self.installation is None or dist.is_community(self.installation.dist)
