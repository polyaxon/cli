from typing import Dict, List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1ArtifactTree(BaseResponseModel):
    files: Optional[Dict[str, StrictStr]]
    dirs: Optional[List[StrictStr]]
    is_done: Optional[bool]
