from typing import Optional

from pydantic import StrictStr

from polyaxon.schemas.base import BaseResponseModel


class V1Auth(BaseResponseModel):
    token: Optional[StrictStr]
