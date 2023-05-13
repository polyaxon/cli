from typing import Dict, List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1ArtifactTree(BaseSchemaModel):
    files: Optional[Dict[str, StrictStr]]
    dirs: Optional[List[StrictStr]]
    is_done: Optional[bool]
