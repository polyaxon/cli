from typing import Optional

from clipped.compact.pydantic import StrictStr
from clipped.config.schema import BaseAllowSchemaModel


class V1RunReferenceCatalog(BaseAllowSchemaModel):
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    name: Optional[StrictStr]
    state: Optional[StrictStr]
