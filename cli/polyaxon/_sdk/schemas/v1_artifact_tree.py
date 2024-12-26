from typing import Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1ArtifactTree(BaseAllowSchemaModel):
    files: Optional[Dict[str, int]] = None
    dirs: Optional[List[StrictStr]] = None
    is_done: Optional[bool] = None
