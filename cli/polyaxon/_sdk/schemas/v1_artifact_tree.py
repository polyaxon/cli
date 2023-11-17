from typing import Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1ArtifactTree(BaseAllowSchemaModel):
    files: Optional[Dict[str, int]]
    dirs: Optional[List[StrictStr]]
    is_done: Optional[bool]
