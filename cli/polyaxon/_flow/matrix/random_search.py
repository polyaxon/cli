from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field, PositiveInt, validator
from clipped.types.ref_or_obj import IntOrRef, RefField

from polyaxon._flow.early_stopping import V1EarlyStopping
from polyaxon._flow.matrix.base import BaseSearchConfig
from polyaxon._flow.matrix.enums import V1MatrixKind
from polyaxon._flow.matrix.params import V1HpParam


class V1RandomSearch(BaseSearchConfig):
    """Random search creates a number of unique experiments by sampling randomly
    from a search space.
    Random search is a competitive method for black-box parameter tuning in machine learning.

    Random search requires a parameter `numRuns`,
    this is essential because Polyaxon needs to know how many experiments to sample.

    Args:
        kind: str, should be equal `grid`
        params: List[Dict[str, [params](/docs/automation/optimization-engine/params/)]]
        concurrency: int, optional
        num_runs: int, optional
        seed: int, optional
        early_stopping: List[[EarlyStopping](/docs/automation/helpers/early-stopping)], optional

    ## YAML usage

    ```yaml
    >>> matrix:
    >>>   kind: random
    >>>   concurrency:
    >>>   params:
    >>>   numRuns:
    >>>   seed:
    >>>   earlyStopping:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import (
    >>>     V1RandomSearch, V1HpLogSpace, V1HpUniform, V1FailureEarlyStopping, V1MetricEarlyStopping
    >>> )
    >>> matrix = V1RandomSearch(
    >>>   num_runs=20,
    >>>   concurrency=2,
    >>>   seed=23,
    >>>   params={"param1": V1HpLogSpace(...), "param2": V1HpUniform(...), ... },
    >>>   early_stopping=[V1FailureEarlyStopping(...), V1MetricEarlyStopping(...)]
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this matrix is a random search.

    If you are using the python client to create the mapping,
    this field is not required and is set by default.

    ```yaml
    >>> matrix:
    >>>   kind: random
    ```

    ### concurrency

    An optional value to set the number of concurrent operations.

    <blockquote class="light">
    This value only makes sense if less or equal to the total number of possible runs.
    </blockquote>

    ```yaml
    >>> matrix:
    >>>   kind: random
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
    >>>   kind: random
    >>>   params:
    >>>     param1:
    >>>        kind: ...
    >>>        value: ...
    >>>     param2:
    >>>        kind: ...
    >>>        value: ...
    ```

    ### numRuns

    Maximum number of runs to start based on the search space defined.

    ```yaml
    >>> matrix:
    >>>   kind: random
    >>>   numRuns: 5
    ```

    ### seed

    Since this algorithm uses random generators,
    if you want to control the seed for the random generator, you can pass a seed.

     ```yaml
    >>> matrix:
    >>>   kind: random
    >>>   seed: 523
    ```

    ### earlyStopping

    A list of early stopping conditions to check for terminating
    all operations managed by the pipeline.
    If one of the early stopping conditions is met,
    a signal will be sent to terminate all running and pending operations.

    ```yaml
    >>> matrix:
    >>>   kind: random
    >>>   earlyStopping: ...
    ```

    For more details please check the
    [early stopping section](/docs/automation/helpers/early-stopping/).

    ## Example

    In this example the random search algorithm will try 20 unique experiments based on the
    search space defined in the params subsection.


    ```yaml
    >>> version: 1.1
    >>> kind: operation
    >>> matrix:
    >>>   kind: random
    >>>   concurrency: 10
    >>>   numRuns: 20
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

    _IDENTIFIER = V1MatrixKind.RANDOM

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    params: Union[Dict[str, V1HpParam], RefField]
    num_runs: Union[PositiveInt, RefField] = Field(alias="numRuns")
    seed: Optional[IntOrRef]
    concurrency: Optional[Union[PositiveInt, RefField]]
    early_stopping: Optional[Union[List[V1EarlyStopping], RefField]] = Field(
        alias="earlyStopping"
    )

    @validator("num_runs", "concurrency", pre=True)
    def check_values(cls, v, field):
        if v and v < 1:
            raise ValueError(f"{field} must be greater than 1, received `{v}` instead.")
        return v
