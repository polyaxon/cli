from typing import Any, Dict, List, Optional, Union

from clipped.compact.pydantic import Field, StrictStr
from clipped.config.patch_strategy import PatchStrategy
from clipped.types.ref_or_obj import RefField

from polyaxon._flow.cache import V1Cache
from polyaxon._flow.params import V1Param
from polyaxon._schemas.base import BaseSchemaModel


class V1Build(BaseSchemaModel):
    """You can configure Polyaxon to automatically trigger a build process anytime
    the component or operation is instantiated.

    the build section allows to dynamically recreate a new docker image
    that will be used to run the main logic.
    The new image is generated automatically and automatically set on the main container,
    the name is based on the project name and the run's uuid, i.e. `project:build-uuid`.

    > **Note**: When the build and matrix sections are used together,
    > a single build operation will be scheduled and will be used for all runs.

    > **Note**: When the build section is defined and an upload is triggered,
    > the uploaded artifacts will be pushed to the build run.

    Args:
        hub_ref: str
        connection: str
        queue: str, optional
        namespace: str, optional
        presets: List[str], optional
        cache: [V1Cache](/docs/automation/helpers/cache/), optional
        params: Dict[str, [V1Param](/docs/core/specification/params/)], optional
        run_patch: Dict, optional
        patch_strategy: str, optional, defaults to post_merge

    ## YAML usage

    ```yaml
    >>> build:
    >>>   hubRef: kaniko
    >>>   connection: registry-connection-name
    >>>   params:
    >>>     context:
    >>>       value: "path/to/context"
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Statuses, V1Build, V1Param
    >>> build = V1Build(
    >>>     hub_ref="kaniko",
    >>>     connection="registry-connection-name",
    >>>     params={
    >>>         "context": V1Param(value="path/to/context"),
    >>>         ...
    >>>     },
    >>> )
    ```

    ## Fields

    ### hubRef

    Polyaxon provides a [Component Hub](/docs/management/component-hub/)
    for hosting versioned components with an access control system to improve
    the productivity of your team.

    To trigger a build based on a component hosted on Polyaxon Component Hub, you can use `hubRef`

    ```yaml
    >>> build:
    >>>   hubRef: kaniko
    ...
    ```

    Or custom hook component

    ```yaml
    >>> build:
    >>>   hubRef: my-component:dev
    ...
    ```

    ### Connection

    The connection to use for pushing the image. Polyaxon will automatically generate a valid image
    based on the project name and the build operation uuid.

    ```yaml
    >>> build:
    >>>   connection: registry-conneciton-name
    ...
    ```

    ### presets

    The [presets](/docs/management/organizations/presets/) to use for the hook operation,
    if provided, it will override the component's presets otherwise
    the presets of the component will be used if available.

    ```yaml
    >>> build:
    >>>   presets: [test]
    ```

    ### queue

    The [queue](/docs/core/scheduling-strategies/queues/) to use.
    If not provided, the default queue will be used.

    ```yaml
    >>> build:
    >>>   queue: agent-name/queue-name
    ```

    If the agent name is not specified, Polyaxon will resolve the name of the queue
    based on the default agent.

    ```yaml
    >>> build:
    >>>   queue: queue-name
    ```

    ### namespace

    > **Note**: Please note that this field is only available in some commercial editions.

    The namespace to use, if not provided, it will default to the agent's namespace.

    ```yaml
    >>> build:
    >>>   namespace: polyaxon
    ```

    ### cache

    The [cache](/docs/automation/helpers/cache/) to use for the build operation,
    if provided, it will override the component's cache otherwise
    the cache of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   cache:
    >>>     disable: false
    >>>     ttl: 100
    ```

    ### params

    The [params](/docs/core/specification/params/) to pass if the handler requires extra params,
    they will be validated against the inputs/outputs.
    If a parameter is passed and the component does not define a corresponding inputs/outputs,
    a validation error will be raised unless the param has the `contextOnly` flag enabled.

    ```yaml
    >>> build:
    >>>   params:
    >>>     param1: {value: 1.1}
    >>>     param2: {value: test}
    >>>   ...
    ```

    Params can be used to pass any number of parameters that the component is expecting.

    Example setting the `context`:

    ```yaml
    >>> build:
    >>>   params:
    >>>     context:
    >>>       value: "{{ globals.artifacts_path }}/repo-name"
    ```

    You can use the params field to define your own image destination with either a
    fixed value like `foo/bar:test` or
    templated with the context information:

    ```yaml
    >>> build:
    >>>   params:
    >>>     destination:
    >>>       value: "org/repo:{{ globals.uuid }}"
    ```

    Or provide the connection under the parameter

    ```yaml
    >>> build:
    >>>   params:
    >>>     destination:
    >>>       value: "org/{{ globals.project_name }}:{{ globals.uuid }}"
    >>>       connection: connection-name
    ```

    Polyaxon will use by default the following destination if no destination parameter is provided:
    `{{ globals.project_name }}:{{ globals.uuid }}` and it will use by default the connection
    defined in the build process.

    ### runPatch

    The run patch provides a way to override information about the component's run section,
    for example the container's resources, the environment section, or the init section.

    The run patch is a dictionary that can modify most of the runtime information and
    will be resolved against the corresponding run kind, in this case
    [V1Job](/docs/experimentation/jobs/).

    ### patchStrategy

    Defines how the compiler should handle keys that are defined on the component,
    or how to merge multiple presets when using the override behavior `-f`.

    There are four strategies:
     * `replace`: replaces all keys with new values if provided.
     * `isnull`: only applies new values if the keys have empty/None values.
     * `post_merge`: applies deep merge where newer values are applied last.
     * `pre_merge`: applies deep merge where newer values are applied first.
    """

    _IDENTIFIER = "build"
    hub_ref: StrictStr = Field(alias="hubRef")
    connection: Optional[StrictStr]
    presets: Optional[Union[List[StrictStr], RefField]]
    queue: Optional[StrictStr]
    namespace: Optional[StrictStr]
    cache: Optional[Union[V1Cache, RefField]]
    params: Optional[Dict[str, Union[V1Param, RefField]]]
    run_patch: Optional[Dict[str, Any]] = Field(alias="runPatch")
    patch_strategy: Optional[Union[PatchStrategy, RefField]] = Field(
        alias="patchStrategy"
    )
