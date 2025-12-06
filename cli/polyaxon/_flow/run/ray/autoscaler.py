from typing import Optional, Union

from clipped.compact.pydantic import Field
from clipped.types.ref_or_obj import RefField

from polyaxon._k8s import k8s_schemas
from polyaxon._schemas.base import BaseSchemaModel


class V1RayAutoscalerOptions(BaseSchemaModel):
    """Ray autoscaler options for configuring automatic scaling behavior.

    Args:
        upscaling_mode: str, optional - "Conservative", "Default", or "Aggressive"
        image_pull_policy: str, optional - "IfNotPresent", "Always", or "Never"
        resources: V1ResourceRequirements, optional - Resources for the autoscaler container

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: raycluster
    >>>   autoscalerOptions:
    >>>     upscalingMode: Default
    >>>     imagePullPolicy: IfNotPresent
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1RayAutoscalerOptions
    >>> autoscaler_options = V1RayAutoscalerOptions(
    >>>     upscaling_mode="Default",
    >>>     image_pull_policy="IfNotPresent",
    >>> )
    ```

    ## Fields

    ### upscalingMode

    Controls how aggressively the autoscaler scales up workers.

    - `Conservative`: Upscaling is rate-limited; the number of pending worker pods
      is at most the size of the Ray cluster.
    - `Default`: Upscaling is not rate-limited.
    - `Aggressive`: An alias for Default; upscaling is not rate-limited.

    ```yaml
    >>> autoscalerOptions:
    >>>   upscalingMode: Default
    ```

    ### imagePullPolicy

    Image pull policy for the autoscaler container.

    ```yaml
    >>> autoscalerOptions:
    >>>   imagePullPolicy: IfNotPresent
    ```

    ### resources

    Resource requirements for the autoscaler container.

    ```yaml
    >>> autoscalerOptions:
    >>>   resources:
    >>>     limits:
    >>>       cpu: "500m"
    >>>       memory: "512Mi"
    >>>     requests:
    >>>       cpu: "250m"
    >>>       memory: "256Mi"
    ```
    """

    _IDENTIFIER = "ray_autoscaler_options"

    upscaling_mode: Optional[str] = Field(alias="upscalingMode", default=None)
    image_pull_policy: Optional[str] = Field(alias="imagePullPolicy", default=None)
    resources: Optional[Union[k8s_schemas.V1ResourceRequirements, RefField]] = None
