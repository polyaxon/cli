from typing import Any, Dict, List, Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1ListBookmarksResponse(BaseSchemaModel):
    count: Optional[int]
    results: Optional[List[Dict[str, Any]]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
