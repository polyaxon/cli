from typing import Dict, List, Optional, Union

from clipped.compact.pydantic import (
    Field,
    StrictStr,
    field_validator,
    validation_always,
    validation_before,
)

from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon._schemas.base import BaseSchemaModel


class BaseServiceConfig(BaseSchemaModel):
    _SWAGGER_FIELDS = {
        "resources",
        "affinity",
        "tolerations",
    }

    image: Optional[StrictStr] = None
    image_tag: Optional[StrictStr] = Field(default=None, alias="imageTag")
    image_pull_policy: Optional[PullPolicy] = Field(
        default=None, alias="imagePullPolicy"
    )
    resources: Optional[Union[k8s_schemas.V1ResourceRequirements, Dict]] = None
    node_selector: Optional[Dict[StrictStr, StrictStr]] = Field(
        default=None, alias="nodeSelector"
    )
    affinity: Optional[Union[k8s_schemas.V1Affinity, Dict]] = None
    tolerations: Optional[List[Union[k8s_schemas.V1Toleration, Dict]]] = None
    image_pull_secrets: Optional[List[StrictStr]] = Field(
        default=None, alias="imagePullSecrets"
    )
    hpa: Optional[Dict] = None

    @field_validator("resources", **validation_always, **validation_before)
    def validate_resources(cls, v):
        return k8s_validation.validate_k8s_resource_requirements(v)

    @field_validator("affinity", **validation_always, **validation_before)
    def validate_affinity(cls, v):
        return k8s_validation.validate_k8s_affinity(v)

    @field_validator("tolerations", **validation_always, **validation_before)
    def validate_tolerations(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_toleration(vi) for vi in v]
