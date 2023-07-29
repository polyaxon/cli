from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1ListBookmarksResponse(BaseResponseModel):
    count: Optional[int]
    results: Optional[List[Dict[str, Any]]]
    previous: Optional[StrictStr]
    next: Optional[StrictStr]
