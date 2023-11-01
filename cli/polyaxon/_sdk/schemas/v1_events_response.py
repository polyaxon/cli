from typing import Any, Dict, List, Optional

from clipped.config.schema import BaseAllowSchemaModel


class V1EventsResponse(BaseAllowSchemaModel):
    data: Optional[List[Dict[str, Any]]]


class V1MultiEventsResponse(BaseAllowSchemaModel):
    data: Optional[Dict[str, Any]]
