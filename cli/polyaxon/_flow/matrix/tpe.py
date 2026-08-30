from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import (
    Field,
    PositiveInt,
    field_validator,
    validation_before,
)
from clipped.types.ref_or_obj import IntOrRef, RefField
from polyaxon._flow.early_stopping import V1EarlyStopping
from polyaxon._flow.matrix.base import BaseSearchConfig
from polyaxon._flow.matrix.enums import V1MatrixKind
from polyaxon._flow.matrix.params import V1HpParam
from polyaxon._flow.matrix.tuner import V1Tuner
from polyaxon._flow.optimization import V1OptimizationMetric


class V1TPE(BaseSearchConfig):
    """Configure Polyaxon's Tree-structured Parzen Estimator search.

    TPE uses completed trials to learn which parts of the search space are more
    promising. It separates better and worse observations, fits a probability
    model for each parameter in both groups, and selects values favored by the
    better model. The first trials use random sampling to collect enough
    observations.

    Unlike grid and random search, later TPE suggestions depend on the metric
    history from earlier trials.

    Args:
        kind: tpe
        params: List[Dict[str, [params](/docs/references/polyaxonfile/orchestration/matrix/params/#discrete-values)]]  # noqa
        metric: V1OptimizationMetric
        max_iterations: int, optional
        concurrency: int, optional
        num_runs: int, optional
        seed: int, optional
        tuner: [V1Tuner](/docs/references/polyaxonfile/orchestration/matrix/tuner/), optional
        early_stopping: List[[EarlyStopping](/docs/references/polyaxonfile/helpers/early-stopping)], optional


    ## YAML usage

    ```yaml
    >>> matrix:
    >>>   kind: tpe
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
    >>>     V1TPE, V1HpLogSpace, V1HpUniform, V1FailureEarlyStopping, V1MetricEarlyStopping
    >>> )
    >>> matrix = V1TPE(
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

    The kind signals to the CLI, client, and other tools that this matrix is TPE.

    If you are using the python client to create the mapping,
    this field is not required and is set by default.

    ```yaml
    >>> matrix:
    >>>   kind: tpe
    ```

    ### concurrency

    An optional value to set the number of concurrent operations.

    <blockquote className="light">
    This value only makes sense if less or equal to the total number of possible runs.
    </blockquote>

    ```yaml
    >>> matrix:
    >>>   kind: tpe
    >>>   concurrency: 2
    ```

    For more details about concurrency management,
    please check the [concurrency section](/docs/references/polyaxonfile/helpers/concurrency/).

    ### params

    A dictionary of `key -> value generator`
    to generate the parameters.

    To learn about all possible
    [params generators](/docs/references/polyaxonfile/orchestration/matrix/params/).

    > The parameters generated will be validated against
    > the component's inputs/outputs definition to check that the values
    > can be passed and have valid types.

    ```yaml
    >>> matrix:
    >>>   kind: tpe
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
    >>>   kind: tpe
    >>>   numRuns: 5
    ```

    ### maxIterations

    Maximum number of iterations to run the process of \\-> suggestions -> training ->\\

    ```yaml
    >>> matrix:
    >>>   kind: tpe
    >>>   maxIterations: 5
    ```

    ### metric

    The metric to optimize during the iterations,
    this is the metric that you want to maximize or minimize.

    ```yaml
    >>> matrix:
    >>>   kind: tpe
    >>>   metric:
    >>>     name: loss
    >>>     optimization: minimize
    ```

    ### seed

    Since this algorithm uses random generators,
    if you want to control the seed for the random generator, you can pass a seed.

     ```yaml
    >>> matrix:
    >>>   kind: tpe
    >>>   seed: 523
    ```

    ### earlyStopping

    A list of early stopping conditions to check for terminating
    all operations managed by the pipeline.
    If one of the early stopping conditions is met,
    a signal will be sent to terminate all running and pending operations.

    ```yaml
    >>> matrix:
    >>>   kind: tpe
    >>>   earlyStopping: ...
    ```

    ### tuner

    The tuner reference (w/o component hub reference) to use.
    The component contains the native TPE logic for creating new suggestions,
    users can override this section to provide a different tuner component.

    ```yaml
    >>> matrix:
    >>>   kind: tpe
    >>>   tuner:
    >>>     hubRef: 'acme/my-tpe-tuner:version'
    ```
    """

    _IDENTIFIER = V1MatrixKind.TPE

    kind: Literal[V1MatrixKind.TPE] = _IDENTIFIER
    max_iterations: Optional[IntOrRef] = Field(alias="maxIterations", default=None)
    metric: V1OptimizationMetric
    params: Union[Dict[str, V1HpParam], RefField]
    num_runs: Union[PositiveInt, RefField] = Field(alias="numRuns", default=None)
    seed: Optional[IntOrRef] = None
    concurrency: Optional[Union[PositiveInt, RefField]] = None
    tuner: Optional[V1Tuner] = None
    early_stopping: Optional[Union[List[V1EarlyStopping], RefField]] = Field(
        alias="earlyStopping", default=None
    )

    @field_validator("num_runs", "concurrency", **validation_before)
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
