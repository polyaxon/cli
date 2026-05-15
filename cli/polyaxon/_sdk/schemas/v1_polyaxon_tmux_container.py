from typing import Any, Dict, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1PolyaxonTmuxContainer(BaseAllowSchemaModel):
    """
    V1PolyaxonTmuxContainer
    """

    image: Optional[StrictStr] = None
    image_tag: Optional[StrictStr] = None
    image_pull_policy: Optional[StrictStr] = None
    resources: Optional[Dict[str, Any]] = None
