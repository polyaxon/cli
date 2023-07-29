from typing import Optional

from clipped.compact.pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1RunReferenceCatalog(BaseResponseModel):
    owner: Optional[StrictStr]
    project: Optional[StrictStr]
    name: Optional[StrictStr]
    state: Optional[StrictStr]
