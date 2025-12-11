from typing import Optional

from clipped.config.schema import BaseAllowSchemaModel


class V1AgentResourcesRequest(BaseAllowSchemaModel):
    namespace: Optional[str] = None
    owner: Optional[str] = None
    uuid: Optional[str] = None
    service: Optional[str] = None
    last_file: Optional[str] = None
    force: Optional[bool] = None
    connection: Optional[str] = None
