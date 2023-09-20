from typing import Dict, List, Optional, Union

from clipped.compact.pydantic import Field, StrictStr, validator

from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon._schemas.base import BaseSchemaModel


class BaseServiceConfig(BaseSchemaModel):
    _SWAGGER_FIELDS = {
        "resources",
        "affinity",
        "tolerations",
    }

    image: Optional[StrictStr]
    image_tag: Optional[StrictStr] = Field(alias="imageTag")
    image_pull_policy: Optional[PullPolicy] = Field(alias="imagePullPolicy")
    resources: Optional[Union[k8s_schemas.V1ResourceRequirements, Dict]]
    node_selector: Optional[Dict[StrictStr, StrictStr]] = Field(alias="nodeSelector")
    affinity: Optional[Union[k8s_schemas.V1Affinity, Dict]]
    tolerations: Optional[List[Union[k8s_schemas.V1Toleration, Dict]]]
    image_pull_secrets: Optional[List[StrictStr]] = Field(alias="imagePullSecrets")
    hpa: Optional[Dict]

    @validator("resources", always=True, pre=True)
    def validate_resources(cls, v):
        return k8s_validation.validate_k8s_resource_requirements(v)

    @validator("affinity", always=True, pre=True)
    def validate_affinity(cls, v):
        return k8s_validation.validate_k8s_affinity(v)

    @validator("tolerations", always=True, pre=True)
    def validate_tolerations(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_toleration(vi) for vi in v]
