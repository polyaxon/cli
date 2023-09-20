from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field, PositiveInt, validator
from clipped.config.schema import skip_partial
from clipped.types.ref_or_obj import RefField

from polyaxon._flow.early_stopping import V1EarlyStopping
from polyaxon._flow.matrix.base import BaseSearchConfig
from polyaxon._flow.matrix.enums import V1MatrixKind
from polyaxon._flow.matrix.params import V1HpParam


def validate_matrix(matrix):
    if not matrix:
        return None

    for key, value in matrix.items():
        if value.is_distribution:
            raise ValueError(
                "`{}` defines a distribution, "
                "and it cannot be used with grid search.".format(key)
            )

    return matrix


class V1GridSearch(BaseSearchConfig):
    """Grid search is essentially an exhaustive search through a manually
    specified set of hyperparameters.

    User can possibly limit the number of experiments and not traverse the whole
    search space created by providing `numRuns`.

    Grid search does not allow the use of distributions,
    and requires that all values of the params definition to
    be [discrete values](/docs/automation/optimization-engine/params/#discrete-values).

    Args:
        kind: str, should be equal `grid`
        params: List[Dict[str, [params](/docs/automation/optimization-engine/params/#discrete-values)]]  # noqa
        concurrency: int, optional
        num_runs: int, optional
        early_stopping: List[[EarlyStopping](/docs/automation/helpers/early-stopping)], optional

    ## YAML usage

    ```yaml
    >>> matrix:
    >>>   kind: grid
    >>>   concurrency:
    >>>   params:
    >>>   numRuns:
    >>>   earlyStopping:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import (
    >>>     V1GridSearch, V1HpLogSpace, V1HpChoice, V1FailureEarlyStopping, V1MetricEarlyStopping
    >>> )
    >>> matrix = V1GridSearch(
    >>>   concurrency=2,
    >>>   params={"param1": V1HpLogSpace(...), "param2": V1HpChoice(...), ... },
    >>>   num_runs=5
    >>>   early_stopping=[V1FailureEarlyStopping(...), V1MetricEarlyStopping(...)]
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this matrix is a grid search.

    If you are using the python client to create the mapping,
    this field is not required and is set by default.

    ```yaml
    >>> matrix:
    >>>   kind: grid
    ```

    ### concurrency

    An optional value to set the number of concurrent operations.

    <blockquote class="light">
    This value only makes sense if less or equal to the total number of possible runs.
    </blockquote>

    ```yaml
    >>> matrix:
    >>>   kind: grid
    >>>   concurrency: 2
    ```

    For more details about concurrency management,
    please check the [concurrency section](/docs/automation/helpers/concurrency/).

    ### params

    A dictionary of `key -> value generator`
    to generate the parameters.

    Gird search can only use
    [discrete value](/docs/automation/optimization-engine/params/#discrete-values).

    > The parameters generated will be validated against
    > the component's inputs/outputs definition to check that the values
    > can be passed and have valid types.

    ```yaml
    >>> matrix:
    >>>   kind: grid
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
    >>>   kind: grid
    >>>   numRuns: 5
    ```

    ### earlyStopping

    A list of early stopping conditions to check for terminating
    all operations managed by the pipeline.
    If one of the early stopping conditions is met,
    a signal will be sent to terminate all running and pending operations.

    ```yaml
    >>> matrix:
    >>>   kind: grid
    >>>   earlyStopping: ...
    ```

    For more details please check the
    [early stopping section](/docs/automation/helpers/early-stopping/).

    ## Example

    This example will define 10 experiments based on the cartesian product
    of `lr` and `dropout` possible values.

    ```yaml
    >>> version: 1.1
    >>> kind: operation
    >>> matrix:
    >>>   kind: grid
    >>>   concurrency: 2
    >>>   params:
    >>>     lr:
    >>>       kind: logspace
    >>>       value: 0.01:0.1:5
    >>>     dropout:
    >>>       kind: choice
    >>>       value: [0.2, 0.5]
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
    >>>   container:
    >>>     image: image:latest
    >>>     command: [python3, train.py]
    >>>     args: ["--batch-size={{ batch_size }}", "--lr={{ lr }}", "--dropout={{ dropout }}"]
    ```
    """

    _IDENTIFIER = V1MatrixKind.GRID

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    params: Union[Dict[str, V1HpParam], RefField]
    num_runs: Optional[Union[PositiveInt, RefField]] = Field(alias="numRuns")
    concurrency: Optional[Union[PositiveInt, RefField]]
    early_stopping: Optional[Union[List[V1EarlyStopping], RefField]] = Field(
        alias="earlyStopping"
    )

    @validator("num_runs", "concurrency", pre=True)
    def check_values(cls, v, field):
        if v and v < 1:
            raise ValueError(f"{field} must be greater than 1, received `{v}` instead.")
        return v

    @validator("params", always=True)
    @skip_partial
    def validate_matrix(cls, params):
        return validate_matrix(params)
