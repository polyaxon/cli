from typing import Any, Dict, List, Optional

from polyaxon.schemas.base import BaseSchemaModel


class V1EventsResponse(BaseSchemaModel):
    data: Optional[List[Dict[str, Any]]]
