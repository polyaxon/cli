from typing import Any, Dict, Optional, Union

from clipped.compact.pydantic import Field, StrictStr
from clipped.types.ref_or_obj import BoolOrRef, IntOrRef, RefField
from clipped.utils.versions import clean_version_post_suffix

from polyaxon import pkg
from polyaxon._containers.pull_policy import PullPolicy
from polyaxon._k8s import k8s_schemas
from polyaxon._schemas.base import BaseSchemaModel


def get_sidecar_resources() -> k8s_schemas.V1ResourceRequirements:
    return k8s_schemas.V1ResourceRequirements(
        limits={"cpu": "1", "memory": "500Mi"},
        requests={"cpu": "0.1", "memory": "60Mi"},
    )


class V1PolyaxonSidecarContainer(BaseSchemaModel):
    """Polyaxon sidecar is a helper container that collects outputs, artifacts,
    and metadata about the main container.

    Polyaxon CE and Polyaxon Agent are deployed with default values for the sidecar container,
    however if you need to control or update one or several aspects
    of how the sidecar container that gets injected, this guide walks through the possible options.

    Args:
        image: str, optional.
        image_tag: str, optional.
        image_pull_policy: str, optional.
        resources: V1ResourceRequirements, optional.
        sleep_interval: int, optional.
        sync_interval: int, optional.
        monitor_logs: bool, optional.
        monitor_spec: bool, optional.

    ## YAML usage

    ```yaml
    >>> sidecar:
    >>>   image: polyaxon/polyaxon-sidecar
    >>>   imageTag: v1.x
    >>>   imagePullPolicy: IfNotPresent
    >>>   resources:
    >>>     requests:
    >>>       memory: "64Mi"
    >>>       cpu: "50m"
    >>>   sleepInterval: 5
    >>>   syncInterval: 60
    >>>   monitorLogs: true
    >>>   monitorSpec: true
    ```

    ## Fields

    ### image

    The container image to use.

    ```yaml
    >>> sidecar:
    >>>   image: polyaxon/polyaxon-sidecar
    ```

    ### imageTag

    The container image tag to use.

    ```yaml
    >>> sidecar:
    >>>   imageTag: dev
    ```

    ### imagePullPolicy

    The image pull policy to use, it must be a valid policy supported by Kubernetes.

    ```yaml
    >>> sidecar:
    >>>   imagePullPolicy: Always
    ```

    ### resources

    The resources requirements to allocate to the container.

    ```yaml
    >>> sidecar:
    >>>   resources:
    >>>     memory: "64Mi"
    >>>     cpu: "50m"
    ```

    ### sleepInterval

    The interval between two consecutive checks, default 10s.

    > **N.B.1**: It's possible to alter this behaviour on per operation level
    > using the sidecar plugin.

    > **N.B.2**: be careful of the trade-off between a large sleep interval and a short interval,
    > you don't want the sidecar to overwhelm the API and Kuberenetes API,
    > and you don't want also the sidecar to penalize your workload with additional latency.

    ```yaml
    >>> sidecar:
    >>>   sleepInterval: 5
    ```

    ### syncInterval

    The interval between two consecutive archiving checks. default 10s.

    > **N.B.1**: It's possible to alter this behaviour on per operation level
    > using the sidecar plugin.

    > **N.B.2**: Only changed files since a previous check are synced.

    > **N.B.3**: If you don't need to access intermediate artifacts while the workload is running,
    > you might set this field to a high value, or `-1` to only trigger
    > this behavior when the workload is done.

    ```yaml
    >>> sidecar:
    >>>   syncInterval: 5
    ```

    ### monitorLogs

    Whether or not to monitor the logs, default `true`.

    ```yaml
    >>> sidecar:
    >>>   monitorLogs: true
    ```

    ### monitorSpec

    Whether or not to monitor the spec, default `true`.

    ```yaml
    >>> sidecar:
    >>>   monitorSpec: true
    ```
    """

    _IDENTIFIER = "polyaxon_sidecar"

    image: Optional[StrictStr]
    image_tag: Optional[StrictStr] = Field(alias="imageTag")
    image_pull_policy: Optional[PullPolicy] = Field(alias="imagePullPolicy")
    sleep_interval: Optional[IntOrRef] = Field(alias="sleepInterval")
    sync_interval: Optional[IntOrRef] = Field(alias="syncInterval")
    monitor_logs: Optional[BoolOrRef] = Field(alias="monitorLogs")
    monitor_spec: Optional[BoolOrRef] = Field(alias="monitorSpec")
    resources: Optional[Union[Dict[str, Any], RefField]]

    def get_image(self):
        image = self.image or "polyaxon/polyaxon-sidecar"
        image_tag = (
            self.image_tag
            if self.image_tag is not None
            else clean_version_post_suffix(pkg.VERSION)
        )
        return "{}:{}".format(image, image_tag) if image_tag else image

    def get_resources(self):
        return self.resources if self.resources else get_sidecar_resources()


def get_default_sidecar_container(
    schema=True,
) -> Union[Dict, V1PolyaxonSidecarContainer]:
    default = {
        "image": "polyaxon/polyaxon-sidecar",
        "imageTag": clean_version_post_suffix(pkg.VERSION),
        "imagePullPolicy": PullPolicy.IF_NOT_PRESENT.value,
        "resources": {
            "limits": {"cpu": "1", "memory": "500Mi"},
            "requests": {"cpu": "0.1", "memory": "60Mi"},
        },
        "sleepInterval": 10,
        "syncInterval": 10,
    }
    if schema:
        return V1PolyaxonSidecarContainer.from_dict(default)
    return default
