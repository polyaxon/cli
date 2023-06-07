from typing import Any, Dict, List, Optional

from polyaxon.schemas.base import BaseResponseModel


class V1EventsResponse(BaseResponseModel):
    data: Optional[List[Dict[str, Any]]]
