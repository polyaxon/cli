from typing import Any, Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1SectionSpec(BaseAllowSchemaModel):
    name: Optional[StrictStr] = None
    is_minimized: Optional[bool] = None
    is_frozen: Optional[str] = None
    columns: Optional[int] = None
    height: Optional[int] = None
    xaxis: Optional[str] = None
    smoothing: Optional[int] = None
    ignore_outliers: Optional[bool] = None
    sample_size: Optional[int] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    page_index: Optional[int] = None
    page_size: Optional[int] = None
