from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import Field, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1SectionSpec(BaseAllowSchemaModel):
    name: Optional[StrictStr]
    is_minimized: Optional[bool]
    columns: Optional[int]
    height: Optional[int]
    widgets: Optional[List[Dict[str, Any]]]
    page_index: Optional[int] = Field(alias="pageIndex")
    page_size: Optional[int] = Field(alias="pageSize")
