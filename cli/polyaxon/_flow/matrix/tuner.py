from typing import Dict, List, Optional, Union

from clipped.compact.pydantic import Field, StrictStr
from clipped.types.ref_or_obj import RefField

from polyaxon._flow.params import V1Param
from polyaxon._schemas.base import BaseSchemaModel


class V1Tuner(BaseSchemaModel):
    """You can configure Polyaxon to use a custom tuner to customize the built-in optimizers.

    The tuner allows you to customize the behavior of the operations that
    generate new suggestions based on the previous observations.

    You can provide a queue or provide presets to override
    the default configuration of the component.
    You can resolve any context information from the main operation inside a tuner,
    like params, globals, ...

    To override the complete behavior users can provide their own component.

    Args:
        hub_ref: str
        queue: List[str], optional
        presets: List[str], optional
        params: Dict[str, [V1Param](/docs/core/specification/params/)], optional

    ## YAML usage

    ```yaml
    >>> tuner:
    >>>   hubRef: acme/custom-tuner
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Statuses, V1Tuner
    >>> tuner = V1Tuner(
    >>>     hub_ref="acme/custom-tuner",
    >>>     queue="agent-name/queue-name",
    >>>     persets=["preset1", "preset2"],
    >>> )
    ```

    ## Fields

    ### hubRef

    For several algorithms, Polyaxon provides built-in tuners. these tuners
    are hosted on the public component hub. Users can customize or
    build different service to generate new suggestions.

    To provide a custom component hosted on Polyaxon Component Hub, you can use `hubRef`

    ```yaml
    >>> tuner:
    >>>   hubRef: acme/optimizer-logic:v1
    ...
    ```

    ### presets

    The [presets](/docs/management/organizations/presets/) to use for the tuner operation,
    if provided, it will override the component's presets otherwise
    the presets of the component will be used if available.

    ```yaml
    >>> tuner:
    >>>   presets: [test]
    ```

    ### queue

    The [queue](/docs/core/scheduling-strategies/queues/) to use.
    If not provided, the default queue will be used.

    ```yaml
    >>> tuner:
    >>>   queue: agent-name/queue-name
    ```

    If the agent name is not specified, Polyaxon will resolve the name of the queue
    based on the default agent.

    ```yaml
    >>> hook:
    >>>   queue: queue-name
    ```

    ### namespace

    > **Note**: Please note that this field is only available in some commercial editions.

    The namespace to use, if not provided, it will default to the agent's namespace.

    ```yaml
    >>> tuner:
    >>>   namespace: polyaxon
    ```

    ### params

    The [params](/docs/core/specification/params/) to pass if the handler requires extra params,
    they will be validated against the inputs/outputs.
    If a parameter is passed and the component does not define a corresponding inputs/outputs,
    a validation error will be raised unless the param has the `contextOnly` flag enabled.

    ```yaml
    >>> tuner:
    >>>   params:
    >>>     param1: {value: 1.1}
    >>>     param2: {value: test}
    >>>   ...
    ```
    """

    _IDENTIFIER = "tuner"

    hub_ref: StrictStr = Field(alias="hubRef")
    presets: Optional[Union[List[StrictStr], RefField]]
    queue: Optional[StrictStr]
    namespace: Optional[StrictStr]
    params: Optional[Union[Dict[str, V1Param], RefField]]
