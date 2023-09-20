from typing import Any, Dict, List, Optional

from clipped.config.schema import BaseAllowSchemaModel


class V1EventsResponse(BaseAllowSchemaModel):
    data: Optional[List[Dict[str, Any]]]
