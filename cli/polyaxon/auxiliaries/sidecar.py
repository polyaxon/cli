#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any, Dict, Optional, Union

from pydantic import Field, StrictStr

from polyaxon import pkg
from polyaxon.containers.pull_policy import PullPolicy
from polyaxon.k8s import k8s_schemas
from polyaxon.schemas.base import BaseSchemaModel
from polyaxon.schemas.fields import BoolOrRef, IntOrRef, RefField


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
    """

    _IDENTIFIER = "polyaxon_sidecar"

    image: Optional[StrictStr]
    image_tag: Optional[StrictStr] = Field(alias="imageTag")
    image_pull_policy: Optional[PullPolicy] = Field(alias="imagePullPolicy")
    sleep_interval: Optional[IntOrRef] = Field(alias="sleepInterval")
    sync_interval: Optional[IntOrRef] = Field(alias="syncInterval")
    monitor_logs: Optional[BoolOrRef] = Field(alias="monitorLogs")
    resources: Optional[Union[Dict[str, Any], RefField]]

    def get_image(self):
        image = self.image or "polyaxon/polyaxon-sidecar"
        image_tag = self.image_tag if self.image_tag is not None else pkg.VERSION
        return "{}:{}".format(image, image_tag) if image_tag else image

    def get_resources(self):
        return self.resources if self.resources else get_sidecar_resources()


def get_default_sidecar_container(schema=True):
    default = {
        "image": "polyaxon/polyaxon-sidecar",
        "imageTag": pkg.VERSION,
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
