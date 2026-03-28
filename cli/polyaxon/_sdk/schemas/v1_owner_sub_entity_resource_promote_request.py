from typing import Optional

from clipped.config.schema import BaseAllowSchemaModel


class V1OwnerSubEntityResourcePromoteRequest(BaseAllowSchemaModel):
    owner: Optional[str] = None
    entity: Optional[str] = None
    uuid: Optional[str] = None
    level: Optional[str] = None
