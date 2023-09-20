from typing import List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class V1ArtifactsMount(BaseSchemaModel):
    _IDENTIFIER = "artifacts_mount"

    name: StrictStr
    paths: Optional[List[StrictStr]]
