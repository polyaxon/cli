from typing import List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field, StrictInt
from clipped.types.ref_or_obj import BoolOrRef, IntOrRef, RefField

from polyaxon._flow.run.enums import V1RunKind
from polyaxon._flow.run.job import V1Job


class V1Service(V1Job):
    """Services are used to launch Tensorboards, Notebooks, JupyterHub apps,
    Streamlit/Voila/Bokeh apps, internal tools,
    and dashboards based on your models and data analysis.

    Args:
        kind: str, should be equal `service`
        environment: [V1Environment](/docs/core/specification/environment/), optional
        connections: List[str], optional
        volumes: List[[Kubernetes Volume](https://kubernetes.io/docs/concepts/storage/volumes/)],
             optional
        init: List[[V1Init](/docs/core/specification/init/)], optional
        sidecars: List[[sidecar containers](/docs/core/specification/sidecars/)], optional
        container: [Kubernetes Container](https://kubernetes.io/docs/concepts/containers/)
        ports: List[int], optional
        rewrite_path: bool, optional
        is_external: bool, optional
        replicas: int, optional

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   environment:
    >>>   connections:
    >>>   volumes:
    >>>   init:
    >>>   sidecars:
    >>>   container:
    >>>   ports:
    >>>   rewritePath:
    >>>   isExternal:
    >>>   int:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Environment, V1Init, V1Service
    >>> from polyaxon import k8s
    >>> service = V1Service(
    >>>     environment=V1Environment(...),
    >>>     connections=["connection-name1"],
    >>>     volumes=[k8s.V1Volume(...)],
    >>>     init=[V1Init(...)],
    >>>     sidecars=[k8s.V1Container(...)],
    >>>     container=k8s.V1Container(...),
    >>>     ports=[6006],
    >>>     rewritePath=True,
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this component's runtime is a service.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: service
    ```

    ### environment

    Optional [environment section](/docs/core/specification/environment/),
    it provides a way to inject pod related information.

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   environment:
    >>>     labels:
    >>>        key1: "label1"
    >>>        key2: "label2"
    >>>      annotations:
    >>>        key1: "value1"
    >>>        key2: "value2"
    >>>      nodeSelector:
    >>>        node_label: node_value
    >>>      ...
    >>>  ...
    ```

     ### connections

     A list of [connection names](/docs/setup/connections/) to resolve for the service.

    <blockquote class="light">
    If you are referencing a connection it must be configured.
    All referenced connections will be checked:

     * If they are accessible in the context of the project of this run

     * If the user running the operation can have access to those connections
    </blockquote>

    After checks, the connections will be resolved and inject any volumes, secrets, configMaps,
    environment variables for your main container to function correctly.

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   connections: [connection1, connection2]
    ```

    ### volumes

    A list of [Kubernetes Volumes](https://kubernetes.io/docs/concepts/storage/volumes/)
    to resolve and mount for your services.

    This is an advanced use-case where configuring a connection is not an option.

    When you add a volume you need to mount it manually to your container(s).

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   volumes:
    >>>     - name: volume1
    >>>       persistentVolumeClaim:
    >>>         claimName: pvc1
    >>>   ...
    >>>   container:
    >>>     name: myapp-container
    >>>     image: busybox:1.28
    >>>     command: ['sh', '-c', 'echo custom init container']
    >>>     volumeMounts:
    >>>     - name: volume1
    >>>       mountPath: /mnt/vol/path
    ```

    ### init

    A list of [init handlers and containers](/docs/core/specification/init/)
    to resolve for the service.

    <blockquote class="light">
     If you are referencing a connection it must be configured.
     All referenced connections will be checked:

     * If they are accessible in the context of the project of this run

     * If the user running the operation can have access to those connections
    </blockquote>

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   init:
    >>>     - artifacts:
    >>>         dirs: ["path/on/the/default/artifacts/store"]
    >>>     - connection: gcs-large-datasets
    >>>       artifacts:
    >>>         dirs: ["data"]
    >>>       container:
    >>>         resources:
    >>>           requests:
    >>>             memory: "256Mi"
    >>>             cpu: "500m"
    >>>     - container:
    >>>       name: myapp-container
    >>>       image: busybox:1.28
    >>>       command: ['sh', '-c', 'echo custom init container']
    ```

    ### sidecars


    A list of [sidecar containers](/docs/core/specification/sidecars/)
    that will be used as sidecars.

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   sidecars:
    >>>     - name: sidecar2
    >>>       image: busybox:1.28
    >>>       command: ['sh', '-c', 'echo sidecar2']
    >>>     - name: sidecar1
    >>>       image: busybox:1.28
    >>>       command: ['sh', '-c', 'echo sidecar1']
    >>>       resources:
    >>>         requests:
    >>>           memory: "128Mi"
    >>>           cpu: "500m"
    ```

    ### container

    The [main Kubernetes Container](https://kubernetes.io/docs/concepts/containers/)
    that will run your experiment training or data processing logic.

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   init:
    >>>     - connection: my-code-repo
    >>>   container:
    >>>     name: tensorflow:2.1
    >>>     command: ["python", "/plx-context/artifacts/my-code-repo/service.py"]
    ```

    ### ports

    The ports to expose for your service.

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   ports: [6006]
    ```

    ### rewritePath

    By default, Polyaxon exposes services with a base url following this pattern:
     `/services/v1/namespace/owner/project/runs/uuid`

    This default behavior works very well for Tensorboards and Notebooks,
    but if you are exposing an API that doesn't handle base urls, you can enable
    this option to rewrite the path and remove that part.

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   rewritePath: true
    ```

    ### isExternal

    By default, Polyaxon will control access to services with the built-in auth mechanism.

    If you need to expose a service without controlling authZ & authN, you can enable this flag.

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   isExternal: true
    ```

    ### replicas

    All services are provisioned with one replica by default.

    This default behavior works very well for Tensorboards, Notebooks,
    and other small service app and dashboards.
    In some cases, and especially in the case of external service,
    you might need to provision more than a single replica,
    you can set the required number of replicas with this field.

    ```yaml
    >>> run:
    >>>   kind: service
    >>>   replicas: 3
    ```
    """

    _IDENTIFIER = V1RunKind.SERVICE

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    ports: Optional[Union[List[StrictInt], RefField]]
    rewrite_path: Optional[BoolOrRef] = Field(alias="rewritePath")
    is_external: Optional[BoolOrRef] = Field(alias="isExternal")
    replicas: Optional[IntOrRef]
