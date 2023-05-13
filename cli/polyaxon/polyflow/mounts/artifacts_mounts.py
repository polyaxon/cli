from typing import List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1ArtifactsMount(BaseSchemaModel):
    _IDENTIFIER = "artifacts_mount"

    name: StrictStr
    paths: Optional[List[StrictStr]]
