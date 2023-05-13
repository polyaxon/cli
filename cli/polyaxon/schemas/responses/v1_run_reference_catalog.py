from typing import Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseSchemaModel


class V1RunReferenceCatalog(BaseSchemaModel):
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    name: Optional[StrictStr]
