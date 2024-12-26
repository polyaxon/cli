from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1ListBookmarksResponse(BaseAllowSchemaModel):
    count: Optional[int] = None
    results: Optional[List[Dict[str, Any]]] = None
    previous: Optional[StrictStr] = None
    next: Optional[StrictStr] = None
