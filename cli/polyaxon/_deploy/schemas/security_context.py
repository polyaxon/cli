from typing import Optional

from clipped.compact.pydantic import Field, StrictInt, StrictStr, root_validator
from clipped.config.schema import skip_partial

from polyaxon._schemas.base import BaseSchemaModel


def validate_security_context(user, group):
    if any([user, group]) and not all([user, group]):
        raise ValueError("Security context requires both `user` and `group` or none.")


class SecurityContextConfig(BaseSchemaModel):
    enabled: Optional[bool]
    run_as_user: Optional[StrictInt] = Field(alias="runAsUser")
    run_as_group: Optional[StrictInt] = Field(alias="runAsGroup")
    fs_group: Optional[StrictInt] = Field(alias="fsGroup")
    fs_group_change_policy: Optional[StrictStr] = Field(alias="fsGroupChangePolicy")
    allow_privilege_escalation: Optional[bool] = Field(alias="allowPrivilegeEscalation")
    run_as_non_root: Optional[bool] = Field(alias="runAsNonRoot")

    @root_validator
    @skip_partial
    def validate_security_context(cls, values):
        validate_security_context(values.get("run_as_user"), values.get("run_as_group"))
        return values
