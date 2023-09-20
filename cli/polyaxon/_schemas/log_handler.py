import base64

from typing import Optional

from clipped.compact.pydantic import StrictStr

from polyaxon._schemas.base import BaseSchemaModel


class V1LogHandler(BaseSchemaModel):
    _IDENTIFIER = "log_handler"

    dsn: Optional[StrictStr]
    environment: Optional[StrictStr]

    @property
    def decoded_dsn(self):
        if self.dsn:
            return base64.b64decode(self.dsn.encode("utf-8")).decode("utf-8")
