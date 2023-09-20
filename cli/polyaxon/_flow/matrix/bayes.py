from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import (
    Field,
    PositiveInt,
    StrictInt,
    root_validator,
    validator,
)
from clipped.config.schema import skip_partial
from clipped.types.ref_or_obj import RefField

from polyaxon._flow.early_stopping import V1EarlyStopping
from polyaxon._flow.matrix.base import BaseSearchConfig
from polyaxon._flow.matrix.enums import (
    AcquisitionFunctions,
    GaussianProcessesKernels,
    V1MatrixKind,
)
from polyaxon._flow.matrix.params import V1HpParam
from polyaxon._flow.matrix.tuner import V1Tuner
from polyaxon._flow.optimization import V1OptimizationMetric
from polyaxon._schemas.base import BaseSchemaModel


class GaussianProcessConfig(BaseSchemaModel):
    _IDENTIFIER = "gaussian_process"

    kernel: Optional[GaussianProcessesKernels] = Field(
        default=GaussianProcessesKernels.MATERN
    )
    length_scale: Optional[float] = Field(default=1.0, alias="lengthScale")
    nu: Optional[float] = Field(default=1.5)
    num_restarts_optimizer: Optional[int] = Field(
        default=0, alias="numRestartsOptimizer"
    )


def validate_utility_function(acquisition_function, kappa, eps):
    condition = AcquisitionFunctions.is_ucb(acquisition_function) and kappa is None
    if condition:
        raise ValueError("the acquisition function `ucb` requires a parameter `kappa`")

    condition = (
        AcquisitionFunctions.is_ei(acquisition_function)
        or AcquisitionFunctions.is_poi(acquisition_function)
    ) and eps is None
    if condition:
        raise ValueError(
            "the acquisition function `{}` requires a parameter `eps`".format(
                acquisition_function
            )
        )


class UtilityFunctionConfig(BaseSchemaModel):  # TODO: Rename to V1UtilityFunction
    _IDENTIFIER = "utility_function"

    acquisition_function: Optional[AcquisitionFunctions] = Field(
        default=AcquisitionFunctions.UCB, alias="acquisitionFunction"
    )
    gaussian_process: Optional[GaussianProcessConfig] = Field(alias="gaussianProcess")
    kappa: Optional[float]
    eps: Optional[float]
    num_warmup: Optional[int] = Field(alias="numWarmup")
    num_iterations: Optional[int] = Field(alias="numIterations")

    @root_validator
    @skip_partial
    def validate_utility_function(cls, values):
        validate_utility_function(
            acquisition_function=values.get("acquisition_function"),
            kappa=values.get("kappa"),
            eps=values.get("eps"),
        )
        return values


def validate_matrix(matrix):
    if not matrix:
        return None

    for key, value in matrix.items():
        if value.is_distribution and not value.is_uniform:
            raise ValueError(
                "`{}` defines a non uniform distribution, "
                "and it cannot be used with bayesian optimization.".format(key)
            )

    return matrix


class V1Bayes(BaseSearchConfig):
    """Bayesian optimization is an extremely powerful technique.
    The main idea behind it is to compute a posterior distribution
    over the objective function based on the data, and then select good points
    to try with respect to this distribution.

    The way Polyaxon performs bayesian optimization is by measuring
    the expected increase in the maximum objective value seen over all
    experiments in the group, given the next point we pick.

    Args:
        kind: string, should be equal to `bayes`
        utility_function: UtilityFunctionConfig
        num_initial_runs: int
        max_iterations: int
        metric: V1OptimizationMetric
        params: List[Dict[str, [params](/docs/automation/optimization-engine/params/#discrete-values)]]  # noqa
        seed: int, optional
        concurrency: int, optional
        tuner: [V1Tuner](/docs/automation/optimization-engine/tuner/), optional
        early_stopping: List[[EarlyStopping](/docs/automation/helpers/early-stopping)], optional


    ## YAML usage

    ```yaml
    >>> matrix:
    >>>   kind: bayes
    >>>   utilityFunction:
    >>>   numInitialRuns:
    >>>   maxIterations:
    >>>   metric:
    >>>   params:
    >>>   seed:
    >>>   concurrency:
    >>>   tuner:
    >>>   earlyStopping:
    ```

    ## Python usage

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import (
    >>>     V1Bayes, V1HpLogSpace, V1HpChoice, V1FailureEarlyStopping, V1MetricEarlyStopping,
    >>>     V1OptimizationMetric, V1Optimization, V1OptimizationResource, UtilityFunctionConfig
    >>> )
    >>> matrix = V1Bayes(
    >>>   concurrency=20,
    >>>   utility_function=UtilityFunctionConfig(...),
    >>>   num_initial_runs=40,
    >>>   max_iterations=20,
    >>>   params={"param1": V1HpLogSpace(...), "param2": V1HpChoice(...), ... },
    >>>   metric=V1OptimizationMetric(name="loss", optimization=V1Optimization.MINIMIZE),
    >>>   early_stopping=[V1FailureEarlyStopping(...), V1MetricEarlyStopping(...)]
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this matrix is bayes.

    If you are using the python client to create the mapping,
    this field is not required and is set by default.

    ```yaml
    >>> matrix:
    >>>   kind: bayes
    ```

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
    >>>   kind: bayes
    >>>   params:
    >>>     param1:
    >>>        kind: ...
    >>>        value: ...
    >>>     param2:
    >>>        kind: ...
    >>>        value: ...
    ```

    ### utilityFunction

    the utility function defines what acquisition function and bayesian process to use.

    ### Acquisition functions

    A couple of acquisition functions can be used: `ucb`, `ei` or `poi`.

     * `ucb`: Upper Confidence Bound,
     * `ei`: Expected Improvement
     * `poi`: Probability of Improvement

    When using `ucb` as acquisition function, a tunable parameter `kappa`
    is also required, to balance exploitation against exploration, increasing kappa
    will make the optimized hyperparameters pursuing exploration.

    When using `ei` or `poi` as acquisition function, a tunable parameter `eps` is also required,
    to balance exploitation against exploration, increasing epsilon will
    make the optimized hyperparameters more spread out across the whole range.

    ### Gaussian process

    Polyaxon allows to tune the gaussian process.

     * `kernel`: `matern` or `rbf`.
     * `lengthScale`: float
     * `nu`: float
     * `numRestartsOptimizer`: int

     ```yaml
     >>> matrix:
     >>>   kind: bayes
     >>>   utility_function:
     >>>     acquisitionFunction: ucb
     >>>     kappa: 1.2
     >>>     gaussianProcess:
     >>>       kernel: matern
     >>>       lengthScale: 1.0
     >>>       nu: 1.9
     >>>       numRestartsOptimizer: 0
     ```

    ### numInitialRuns

    the initial iteration of random experiments is required to create a seed of observations.

    This initial random results are used by the algorithm to update
    the regression model for generating the next suggestions.

    ```yaml
    >>> matrix:
    >>>   kind: bayes
    >>>   numInitialRuns: 40
    ```

    ### maxIterations

    After creating the first set of random observations,
    the algorithm will use these results to update
    the regression model and suggest a new experiment to run.

    Every time an experiment is done,
    the results are used as an observation and are appended
    to the historical values so that the algorithm can use all
    the observations again to suggest more experiments to run.

    The algorithm will keep suggesting more experiments and adding
    their results as an observation, every time we make a new observation,
    i.e. an experiment finishes and reports the results to the platform,
    the results are appended to the historical values, and then used to make a better suggestion.

    ```yaml
    >>> matrix:
    >>>   kind: bayes
    >>>   maxIterations: 15
    ```

    This configuration will make 15 suggestions based on the historical values,
    every time an observation is made is appended to the historical values
    to make better subsequent suggestions.

    ### metric

    The metric to optimize during the iterations,
    this is the metric that you want to maximize or minimize.

    ```yaml
    >>> matrix:
    >>>   kind: bayes
    >>>   metric:
    >>>     name: loss
    >>>     optimization: minimize
    ```

    ### seed

    Since this algorithm uses random generators,
    if you want to control the seed for the random generator, you can pass a seed.

     ```yaml
    >>> matrix:
    >>>   kind: bayes
    >>>   seed: 523
    ```

    ### concurrency

    An optional value to set the number of concurrent operations.

    <blockquote class="light">
    This value only makes sense if less or equal to the total number of possible runs.
    </blockquote>

    ```yaml
    >>> matrix:
    >>>   kind: bayes
    >>>   concurrency: 20
    ```

    For more details about concurrency management,
    please check the [concurrency section](/docs/automation/helpers/concurrency/).

    ### earlyStopping

    A list of early stopping conditions to check for terminating
    all operations managed by the pipeline.
    If one of the early stopping conditions is met,
    a signal will be sent to terminate all running and pending operations.

    ```yaml
    >>> matrix:
    >>>   kind: bayes
    >>>   earlyStopping: ...
    ```

    For more details please check the
    [early stopping section](/docs/automation/helpers/early-stopping/).

    ### tuner

    The tuner reference (w/o component hub reference) to use.
    The component contains the logic for creating new suggestions based on bayesian optimization,
    users can override this section to provide a different tuner component.

    ```yaml
    >>> matrix:
    >>>   kind: bayes
    >>>   tuner:
    >>>     hubRef: 'acme/my-bo-tuner:version'
    ```

    ## Example

    This is an example of using bayesian search for hyperparameter tuning:

    ```yaml
    >>> matrix:
    >>>   kind: bayes
    >>>   concurrency: 5
    >>>   maxIterations: 15
    >>>   numInitialTrials: 30
    >>>   metric:
    >>>     name: loss
    >>>     optimization: minimize
    >>>   utilityFunction:
    >>>     acquisitionFunction: ucb
    >>>     kappa: 1.2
    >>>     gaussianProcess:
    >>>       kernel: matern
    >>>       lengthScale: 1.0
    >>>       nu: 1.9
    >>>       numRestartsOptimizer: 0
    >>>   params:
    >>>     lr:
    >>>       kind: uniform
    >>>       value: [0, 0.9]
    >>>     dropout:
    >>>       kind: choice
    >>>       value: [0.25, 0.3]
    >>>     activation:
    >>>       kind: pchoice
    >>>       value: [[relu, 0.1], [sigmoid, 0.8]]
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
    >>>     args: [
    >>>         "--batch-size={{ batch_size }}",
    >>>         "--lr={{ lr }}",
    >>>         "--dropout={{ dropout }}",
    >>>         "--activation={{ activation }}"
    ```
    """

    _IDENTIFIER = V1MatrixKind.BAYES

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    utility_function: Optional[UtilityFunctionConfig] = Field(alias="utilityFunction")
    num_initial_runs: Union[PositiveInt, RefField] = Field(alias="numInitialRuns")
    max_iterations: Union[PositiveInt, RefField] = Field(alias="maxIterations")
    metric: V1OptimizationMetric
    params: Union[Dict[str, V1HpParam], RefField]
    seed: Optional[Union[StrictInt, RefField]]
    concurrency: Optional[Union[PositiveInt, RefField]]
    tuner: Optional[Union[V1Tuner, RefField]]
    early_stopping: Optional[Union[List[V1EarlyStopping], RefField]] = Field(
        alias="earlyStopping"
    )

    def create_iteration(self, iteration: Optional[int] = None) -> int:
        if iteration is None:
            return 0
        return iteration + 1

    def should_reschedule(self, iteration):
        """Return a boolean to indicate if we need to reschedule another iteration."""
        return iteration < self.max_iterations

    @validator("params", always=True)
    @skip_partial
    def validate_matrix(cls, params):
        return validate_matrix(params)
