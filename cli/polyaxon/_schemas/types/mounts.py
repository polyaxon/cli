from typing import Optional

from clipped.compact.pydantic import Field, StrictStr

from polyaxon._schemas.types.base import BaseTypeConfig


class V1Mount(BaseTypeConfig):
    _IDENTIFIER = "mount"

    path_from: Optional[StrictStr] = Field(alias="from", default=None)
    path_to: Optional[StrictStr] = Field(alias="to", default=None)
