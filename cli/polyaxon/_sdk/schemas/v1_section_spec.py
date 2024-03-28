from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import Field, StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1SectionSpec(BaseAllowSchemaModel):
    name: Optional[StrictStr]
    is_minimized: Optional[bool]
    is_frozen: Optional[str]
    columns: Optional[int]
    height: Optional[int]
    xaxis: Optional[str]
    smoothing: Optional[int]
    ignore_outliers: Optional[bool]
    sample_size: Optional[int]
    widgets: Optional[List[Dict[str, Any]]]
    page_index: Optional[int]
    page_size: Optional[int]
