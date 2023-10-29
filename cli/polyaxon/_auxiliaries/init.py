from typing import Dict, Optional, Union

from clipped.compact.pydantic import Field, StrictStr, validator
from clipped.utils.versions import clean_version_post_suffix

from polyaxon import pkg
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon._schemas.base import BaseSchemaModel


def get_init_resources() -> k8s_schemas.V1ResourceRequirements:
    return k8s_schemas.V1ResourceRequirements(
        limits={"cpu": "1", "memory": "500Mi"},
        requests={"cpu": "0.1", "memory": "60Mi"},
    )


class V1PolyaxonInitContainer(BaseSchemaModel):
    """Polyaxon init is a helper container that initialize the environment
    required for the main container to function correctly.

    Polyaxon CE and Polyaxon Agent are deployed with default values for the init container,
    however if you need to control or update one or several aspects
    of how the init container that gets injected, this guide walks through the possible options.

    Args:
        image: str, optional.
        image_tag: str, optional.
        image_pull_policy: str, optional.
        resources: V1ResourceRequirements, optional.

    ## YAML usage

    ```yaml
    >>> init:
    >>>   image: polyaxon/polyaxon-sidecar
    >>>   imageTag: v1.x
    >>>   imagePullPolicy: IfNotPresent
    >>>   resources:
    >>>     requests:
    >>>       memory: "64Mi"
    >>>       cpu: "50m"
    ```

    ## Fields

    ### image

    The container image to use.

    ```yaml
    >>> init:
    >>>   image: polyaxon/polyaxon-sidecar
    ```

    ### imageTag

    The container image tag to use.

    ```yaml
    >>> init:
    >>>   imageTag: dev
    ```

    ### imagePullPolicy

    The image pull policy to use, it must be a valid policy supported by Kubernetes.

    ```yaml
    >>> init:
    >>>   imagePullPolicy: Always
    ```

    ### resources

    The resources requirements to allocate to the container.

    ```yaml
    >>> init:
    >>>   resources:
    >>>     memory: "64Mi"
    >>>     cpu: "50m"
    ```

    > **N.B.1**: Resources are applied to all instances of
    > the init container within the same pod.

    > **N.B.2**: It's possible to alter this behaviour on per operation level
    > using the init section.
    """

    _IDENTIFIER = "container"
    _SWAGGER_FIELDS = ["resources"]

    image: Optional[StrictStr]
    image_tag: Optional[StrictStr] = Field(alias="imageTag")
    image_pull_policy: Optional[PullPolicy] = Field(alias="imagePullPolicy")
    resources: Optional[Union[k8s_schemas.V1ResourceRequirements, Dict]]

    @validator("resources", always=True, pre=True)
    def validate_resources(cls, v) -> k8s_schemas.V1ResourceRequirements:
        return k8s_validation.validate_k8s_resource_requirements(v)

    def get_image(self) -> str:
        image = self.image or "polyaxon/polyaxon-init"
        image_tag = (
            self.image_tag
            if self.image_tag is not None
            else clean_version_post_suffix(pkg.VERSION)
        )
        return "{}:{}".format(image, image_tag) if image_tag else image

    def get_resources(self) -> k8s_schemas.V1ResourceRequirements:
        return self.resources if self.resources else get_init_resources()


def get_default_init_container(
    schema: bool = True,
) -> Union[Dict, V1PolyaxonInitContainer]:
    default = {
        "image": "polyaxon/polyaxon-init",
        "imageTag": clean_version_post_suffix(pkg.VERSION),
        "imagePullPolicy": PullPolicy.IF_NOT_PRESENT.value,
        "resources": {
            "limits": {"cpu": "1", "memory": "500Mi"},
            "requests": {"cpu": "0.1", "memory": "60Mi"},
        },
    }
    if schema:
        return V1PolyaxonInitContainer.from_dict(default)
    return default
