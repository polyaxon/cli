from typing import Optional

from clipped.compact.pydantic import (
    Field,
    StrictInt,
    StrictStr,
    model_validator,
    validation_after,
)
from clipped.config.schema import skip_partial

from polyaxon._schemas.base import BaseSchemaModel


class SecurityContextConfig(BaseSchemaModel):
    enabled: Optional[bool] = None
    run_as_user: Optional[StrictInt] = Field(alias="runAsUser", default=None)
    run_as_group: Optional[StrictInt] = Field(alias="runAsGroup", default=None)
    fs_group: Optional[StrictInt] = Field(alias="fsGroup", default=None)
    fs_group_change_policy: Optional[StrictStr] = Field(
        alias="fsGroupChangePolicy", default=None
    )
    allow_privilege_escalation: Optional[bool] = Field(
        alias="allowPrivilegeEscalation", default=None
    )
    run_as_non_root: Optional[bool] = Field(alias="runAsNonRoot", default=None)

    @model_validator(**validation_after)
    @skip_partial
    def validate_security_context(cls, values):
        user = cls.get_value_for_key("run_as_user", values)
        group = cls.get_value_for_key("run_as_group", values)
        if any([user, group]) and not all([user, group]):
            raise ValueError(
                "Security context requires both `user` and `group` or none."
            )
        return values
