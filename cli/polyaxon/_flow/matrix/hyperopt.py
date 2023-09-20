from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import Field, PositiveInt, validator
from clipped.types.ref_or_obj import IntOrRef, RefField
from clipped.utils.enums import PEnum

from polyaxon._flow.early_stopping import V1EarlyStopping
from polyaxon._flow.matrix.base import BaseSearchConfig
from polyaxon._flow.matrix.enums import V1MatrixKind
from polyaxon._flow.matrix.params import V1HpParam
from polyaxon._flow.matrix.tuner import V1Tuner
from polyaxon._flow.optimization import V1OptimizationMetric


class V1HyperoptAlgorithms(str, PEnum):
    TPE = "tpe"
    RAND = "rand"
    ANNEAL = "anneal"


class V1Hyperopt(BaseSearchConfig):
    """Hyperopt is a search algorithm that is backed by the
    [Hyperopt](http://hyperopt.github.io/hyperopt/) library
    to perform sequential model-based hyperparameter optimization.

    the Hyperopt integration exposes 3 algorithms: `tpe`, `rand`, `anneal`.

    Args:
        kind: hyperopt
        algorithm: str, one of tpe, rand, anneal
        params: List[Dict[str, [params](/docs/automation/optimization-engine/params/#discrete-values)]]  # noqa
        metric: V1OptimizationMetric
        max_iterations: int, optional
        concurrency: int, optional
        num_runs: int, optional
        seed: int, optional
        tuner: [V1Tuner](/docs/automation/optimization-engine/tuner/), optional
        early_stopping: List[[EarlyStopping](/docs/automation/helpers/early-stopping)], optional


    ## YAML usage

    ```yaml
    >>> matrix:
    >>>   kind: hyperopt
    >>>   algorithm:
    >>>   maxIterations:
    >>>   metric:
    >>>   concurrency:
    >>>   params:
    >>>   numRuns:
    >>>   seed:
    >>>   tuner:
    >>>   earlyStopping:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import (
    >>>     V1Hyperopt, V1HpLogSpace, V1HpUniform, V1FailureEarlyStopping, V1MetricEarlyStopping
    >>> )
    >>> matrix = V1Hyperopt(
    >>>   algorithm="tpe",
    >>>   num_runs=20,
    >>>   concurrency=2,
    >>>   seed=23,
    >>>   metric=V1OptimizationMetric(name="loss", optimization=V1Optimization.MINIMIZE),
    >>>   params={"param1": V1HpLogSpace(...), "param2": V1HpUniform(...), ... },
    >>>   early_stopping=[V1FailureEarlyStopping(...), V1MetricEarlyStopping(...)]
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this matrix is hyperopt.

    If you are using the python client to create the mapping,
    this field is not required and is set by default.

    ```yaml
    >>> matrix:
    >>>   kind: hyperopt
    ```

    ### algorithm

    The algorithm to use from the hyperopt library, the supported
    algorithms: `tpe`, `rand`, `anneal`.

    ```yaml
    >>> matrix:
    >>>   kind: hyperopt
    >>>   algorithm: anneal
    ```

    ### concurrency

    An optional value to set the number of concurrent operations.

    <blockquote class="light">
    This value only makes sense if less or equal to the total number of possible runs.
    </blockquote>

    ```yaml
    >>> matrix:
    >>>   kind: hyperopt
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
    >>>   kind: hyperopt
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
    >>>   kind: hyperopt
    >>>   numRuns: 5
    ```

    ### maxIterations

    Maximum number of iterations to run the process of \\-> suggestions -> training ->\\

    ```yaml
    >>> matrix:
    >>>   kind: hyperopt
    >>>   maxIterations: 5
    ```

    ### metric

    The metric to optimize during the iterations,
    this is the metric that you want to maximize or minimize.

    ```yaml
    >>> matrix:
    >>>   kind: hyperopt
    >>>   metric:
    >>>     name: loss
    >>>     optimization: minimize
    ```

    ### seed

    Since this algorithm uses random generators,
    if you want to control the seed for the random generator, you can pass a seed.

     ```yaml
    >>> matrix:
    >>>   kind: hyperopt
    >>>   seed: 523
    ```

    ### earlyStopping

    A list of early stopping conditions to check for terminating
    all operations managed by the pipeline.
    If one of the early stopping conditions is met,
    a signal will be sent to terminate all running and pending operations.

    ```yaml
    >>> matrix:
    >>>   kind: hyperopt
    >>>   earlyStopping: ...
    ```

    ### tuner

    The tuner reference (w/o component hub reference) to use.
    The component contains the logic for creating new suggestions based on hyperopt library,
    users can override this section to provide a different tuner component.

    ```yaml
    >>> matrix:
    >>>   kind: hyperopt
    >>>   tuner:
    >>>     hubRef: 'acme/my-hyperopt-tuner:version'
    ```
    """

    _IDENTIFIER = V1MatrixKind.HYPEROPT

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    max_iterations: Optional[IntOrRef] = Field(alias="maxIterations")
    metric: V1OptimizationMetric
    algorithm: Optional[V1HyperoptAlgorithms]
    params: Union[Dict[str, V1HpParam], RefField]
    num_runs: Union[PositiveInt, RefField] = Field(alias="numRuns")
    seed: Optional[IntOrRef]
    concurrency: Optional[Union[PositiveInt, RefField]]
    tuner: Optional[V1Tuner]
    early_stopping: Optional[Union[List[V1EarlyStopping], RefField]] = Field(
        alias="earlyStopping"
    )

    @validator("num_runs", "concurrency", pre=True)
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
        if not self.max_iterations:
            return True
        return iteration < self.max_iterations
