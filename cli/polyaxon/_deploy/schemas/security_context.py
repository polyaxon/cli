from typing import Optional

from clipped.compact.pydantic import Field, StrictInt, StrictStr
from clipped.config.schema import skip_partial_after
from polyaxon._schemas.base import BaseSchemaModel


class SecurityContextConfig(BaseSchemaModel):
    enabled: Optional[bool] = None
    apply_to_runs: Optional[bool] = Field(alias="applyToRuns", default=None)
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

    @skip_partial_after
    def validate_security_context(self):
        user = self.run_as_user
        group = self.run_as_group
        if any([user, group]) and not all([user, group]):
            raise ValueError(
                "Security context requires both `user` and `group` or none."
            )
        return self
