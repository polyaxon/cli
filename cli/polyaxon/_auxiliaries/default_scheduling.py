from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from clipped.compact.pydantic import Field, StrictStr, validator

from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon._schemas.base import BaseSchemaModel

if TYPE_CHECKING:
    from polyaxon._flow import V1Environment


class V1DefaultScheduling(BaseSchemaModel):
    _IDENTIFIER = "default_scheduling"
    _SWAGGER_FIELDS = ["affinity", "tolerations"]

    node_selector: Optional[Dict[StrictStr, StrictStr]] = Field(alias="nodeSelector")
    affinity: Optional[Union[k8s_schemas.V1Affinity, Dict]]
    tolerations: Optional[List[Union[k8s_schemas.V1Toleration, Dict]]]
    image_pull_secrets: Optional[List[StrictStr]] = Field(alias="imagePullSecrets")

    @validator("affinity", always=True, pre=True)
    def validate_affinity(cls, v) -> k8s_schemas.V1Affinity:
        return k8s_validation.validate_k8s_affinity(v)

    @validator("tolerations", always=True, pre=True)
    def validate_tolerations(cls, v) -> List[k8s_schemas.V1Toleration]:
        if not v:
            return v
        return [k8s_validation.validate_k8s_toleration(vi) for vi in v]

    @staticmethod
    def get_service_environment(
        service: Any,
        default_scheduling: "V1DefaultScheduling",
    ) -> "V1Environment":
        from polyaxon._flow import V1Environment

        env = V1Environment.construct()
        if service and service.node_selector:
            env.node_selector = service.node_selector
        elif default_scheduling and default_scheduling.node_selector:
            env.node_selector = default_scheduling.node_selector
        if service and service.affinity:
            env.affinity = service.affinity
        elif default_scheduling and default_scheduling.affinity:
            env.affinity = default_scheduling.affinity
        if service and service.tolerations:
            env.tolerations = service.tolerations
        elif default_scheduling and default_scheduling.tolerations:
            env.tolerations = default_scheduling.tolerations
        if service and service.image_pull_secrets:
            env.image_pull_secrets = service.image_pull_secrets
        elif default_scheduling and default_scheduling.image_pull_secrets:
            env.image_pull_secrets = default_scheduling.image_pull_secrets

        return env
