from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1ListBookmarksResponse(BaseAllowSchemaModel):
    count: Optional[int]
    results: Optional[List[Dict[str, Any]]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
