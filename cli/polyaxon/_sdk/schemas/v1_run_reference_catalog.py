from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1RunReferenceCatalog(BaseAllowSchemaModel):
    owner: Optional[StrictStr] = None
    project: Optional[StrictStr] = None
    name: Optional[StrictStr] = None
    state: Optional[StrictStr] = None
