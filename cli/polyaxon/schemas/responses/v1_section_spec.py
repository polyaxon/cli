from typing import Any, Dict, List, Optional

from pydantic import Field, StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1SectionSpec(BaseResponseModel):
    name: Optional[StrictStr]
    is_minimized: Optional[bool]
    columns: Optional[int]
    height: Optional[int]
    widgets: Optional[List[Dict[str, Any]]]
    page_index: Optional[int] = Field(alias="pageIndex")
    page_size: Optional[int] = Field(alias="pageSize")
