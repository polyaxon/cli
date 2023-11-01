from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field, PositiveInt, validator
from clipped.types.ref_or_obj import IntOrRef, RefField

from polyaxon._flow.early_stopping import V1EarlyStopping
from polyaxon._flow.matrix.base import BaseSearchConfig
from polyaxon._flow.matrix.enums import V1MatrixKind
from polyaxon._flow.matrix.params import V1HpParam
from polyaxon._flow.matrix.tuner import V1Tuner


class V1Iterative(BaseSearchConfig):
    """To build a custom optimization algorithm, this interface lets you create an iterative
    process for creating suggestions and training your model based on those suggestions

    The iterative process expect a user defined a tuner that will generate the suggestions for
    running the component.

    Args:
        kind: str, should be equal `iterative`
        max_iterations: int
        params: List[Dict[str, [params](/docs/automation/optimization-engine/params/)]]
        concurrency: int, optional
        seed: int, optional
        tuner: [V1Tuner](/docs/automation/optimization-engine/tuner/), optional
        early_stopping: List[[EarlyStopping](/docs/automation/helpers/early-stopping)], optional

    ## YAML usage

    ```yaml
    >>> matrix:
    >>>   kind: iterative
    >>>   concurrency:
    >>>   params:
    >>>   maxIterations:
    >>>   seed:
    >>>   tuner:
    >>>   earlyStopping:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import (
    >>>     V1Iterative,
    >>>     V1HpLogSpace,
    >>>     V1HpUniform,
    >>>     V1FailureEarlyStopping,
    >>>     V1MetricEarlyStopping,
    >>>     V1Tuner,
    >>> )
    >>> matrix = V1Iterative(
    >>>   max_iterations=20,
    >>>   concurrency=2,
    >>>   seed=23,
    >>>   params={"param1": V1HpLogSpace(...), "param2": V1HpUniform(...), ... },
    >>>   early_stopping=[V1FailureEarlyStopping(...), V1MetricEarlyStopping(...)],
    >>>   tuner=V1Tuner(hub_ref="org/my-suggestion-component")
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this matrix is an iterative process.

    If you are using the python client to create the mapping,
    this field is not required and is set by default.

    ```yaml
    >>> matrix:
    >>>   kind: iterative
    ```

    ### concurrency

    An optional value to set the number of concurrent operations.

    <blockquote class="light">
    This value only makes sense if less or equal to the total number of possible runs.
    </blockquote>

    ```yaml
    >>> matrix:
    >>>   kind: iterative
    >>>   concurrency: 2
    ```

    For more details about concurrency management,
    please check the [concurrency section](/docs/automation/helpers/concurrency/).

    ### params

    A dictionary of `key -> value generator`
    to generate the parameters.

    To learn about all possible
    [params generators](/docs/automation/optimization-engine/params/).

    > The parameters generated will be validated against
    > the component's inputs/outputs definition to check that the values
    > can be passed and have valid types.

    ```yaml
    >>> matrix:
    >>>   kind: iterative
    >>>   params:
    >>>     param1:
    >>>        kind: ...
    >>>        value: ...
    >>>     param2:
    >>>        kind: ...
    >>>        value: ...
    ```

    ### maxIterations

    Maximum number of iterations to run the process of \\-> suggestions -> training ->\\

    ```yaml
    >>> matrix:
    >>>   kind: iterative
    >>>   maxIterations: 5
    ```

    ### seed

    Since this algorithm uses random generators,
    if you want to control the seed for the random generator, you can pass a seed.

     ```yaml
    >>> matrix:
    >>>   kind: iterative
    >>>   seed: 523
    ```

    ### earlyStopping

    A list of early stopping conditions to check for terminating
    all operations managed by the pipeline.
    If one of the early stopping conditions is met,
    a signal will be sent to terminate all running and pending operations.

    ```yaml
    >>> matrix:
    >>>   kind: iterative
    >>>   earlyStopping: ...
    ```

    For more details please check the
    [early stopping section](/docs/automation/helpers/early-stopping/).

    ### tuner

    The tuner reference definition (with a component hub reference) to use.
    The component contains the logic for creating new suggestions.

    ```yaml
    >>> matrix:
    >>>   kind: iterative
    >>>   tuner:
    >>>     hubRef: acme/suggestion-logic:v1
    ```

    ## Example

    In this example the iterative process will try run 5 iterations generating new experiments
    based on the search space defined in the params subsection.


    ```yaml
    >>> version: 1.1
    >>> kind: operation
    >>> matrix:
    >>>   kind: iterative
    >>>   concurrency: 10
    >>>   maxIterations: 5
    >>>   tuner:
    >>>     hubRef: my-suggestion-component
    >>>   params:
    >>>     lr:
    >>>       kind: logspace
    >>>       value: 0.01:0.1:5
    >>>     dropout:
    >>>       kind: choice
    >>>       value: [0.2, 0.5]
    >>>    activation:
    >>>       kind: pchoice
    >>>       value: [[elu, 0.1], [relu, 0.2], [sigmoid, 0.7]]
    >>>    early_stopping:
    >>>      - metric: accuracy
    >>>        value: 0.9
    >>>        optimization: maximize
    >>>      - metric: loss
    >>>        value: 0.05
    >>>        optimization: minimize
    >>> component:
    >>>   inputs:
    >>>     - name: batch_size
    >>>       type: int
    >>>       isOptional: true
    >>>       value: 128
    >>>     - name: lr
    >>>       type: float
    >>>     - name: dropout
    >>>       type: float
    >>>     - name: activation
    >>>       type: str
    >>>   container:
    >>>     image: image:latest
    >>>     command: [python3, train.py]
    >>>     args: [
    >>>         "--batch-size={{ batch_size }}",
    >>>         "--lr={{ lr }}",
    >>>         "--dropout={{ dropout }}",
    >>>         "--activation={{ activation }}"
    >>>     ]
    ```
    """

    _IDENTIFIER = V1MatrixKind.ITERATIVE

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    params: Optional[Union[Dict[str, V1HpParam], RefField]]
    max_iterations: Union[PositiveInt, RefField] = Field(alias="maxIterations")
    seed: Optional[IntOrRef]
    concurrency: Optional[Union[PositiveInt, RefField]]
    tuner: Optional[V1Tuner]
    early_stopping: Optional[Union[List[V1EarlyStopping], RefField]] = Field(
        alias="earlyStopping"
    )

    @validator("max_iterations", "concurrency", pre=True)
    def check_values(cls, v, field):
        if v and v < 1:
            raise ValueError(f"{field} must be greater than 1, received `{v}` instead.")
        return v

    def create_iteration(self, iteration: Optional[int] = None) -> int:
        if iteration is None:
            return 0
        return iteration + 1

    def should_reschedule(self, iteration):
        """Return a boolean to indicate if we need to reschedule another iteration."""
        return iteration < self.max_iterations
