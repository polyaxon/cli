from typing import Optional, Union
from typing_extensions import Annotated, Literal

from clipped.compact.pydantic import Field, StrictFloat, StrictStr
from clipped.types.ref_or_obj import BoolOrRef, FloatOrRef, IntOrRef

from polyaxon._flow.optimization import V1Optimization
from polyaxon._schemas.base import BaseSchemaModel


class V1MedianStoppingPolicy(BaseSchemaModel):
    _IDENTIFIER = "median"
    _USE_DISCRIMINATOR = True

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    evaluation_interval: IntOrRef = Field(alias="evaluationInterval")
    min_interval: Optional[IntOrRef] = Field(alias="minInterval")
    min_samples: Optional[IntOrRef] = Field(alias="minSamples")


class V1TruncationStoppingPolicy(BaseSchemaModel):
    _IDENTIFIER = "truncation"

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    percent: FloatOrRef
    evaluation_interval: IntOrRef = Field(alias="evaluationInterval")
    min_interval: Optional[IntOrRef] = Field(alias="minInterval")
    min_samples: Optional[IntOrRef] = Field(alias="minSamples")
    include_succeeded: Optional[BoolOrRef] = Field(alias="includeSucceeded")


class V1DiffStoppingPolicy(BaseSchemaModel):
    _IDENTIFIER = "diff"

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    percent: FloatOrRef
    evaluation_interval: IntOrRef = Field(alias="evaluationInterval")
    min_interval: Optional[IntOrRef] = Field(alias="minInterval")
    min_samples: Optional[IntOrRef] = Field(alias="minSamples")


V1EarlyStoppingPolicy = Annotated[
    Union[V1MedianStoppingPolicy, V1TruncationStoppingPolicy, V1DiffStoppingPolicy],
    Field(discriminator="kind", alias="earlyStopping"),
]


class V1MetricEarlyStopping(BaseSchemaModel):
    """Metric early stopping is an early stopping strategy based on metrics of runs,
    it allows to terminate a dag, a mapping, or hyperparameter tuning when a run's metric(s)
    meet(s) one or multiple conditions.

    If no policy is set and a metric early stopping condition is met the pipeline will be marked
    as succeeded and all pending or running operations will be stopped.

    If a policy is set only the runs that validate the policy will be stopped.

    Args:
        kind: str, should be equal to `metric_early_stopping`
        metric: str
        value: float
        optimization: Union["maximize", "minimize"]
        policy: Union[V1MedianStoppingPolicy, V1TruncationStoppingPolicy, V1DiffStoppingPolicy],
             optional

    ## YAML usage

    ```yaml
    >>> earlyStopping:
    >>>   - kind: metric_early_stopping
    >>>     metric: loss
    >>>     value: 0.001
    >>>     optimization: minimize
    >>>   - kind: metric_early_stopping
    >>>     metric: accuaracy
    >>>     value: 0.9
    >>>     optimization: maximize
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1MetricEarlyStopping, V1Optimization
    >>> early_stopping = [
    >>>     V1MetricEarlyStopping(metric="loss", optimization=V1Optimization.MINIMIZE),
    >>>     V1MetricEarlyStopping(metric="accuracy", optimization=V1Optimization.MAXIMIZE),
    >>> ]
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools
    that this early stopping is `metric_early_stopping`.

    If you are using the python client to create the early stopping,
    this field is not required and is set by default.

    ```yaml
    >>> earlyStopping:
    >>>   - kind: metric_early_stopping
    ```

    ### metric

    The metric to track for checking the early stopping condition.
    This metric should be logged using one of the tracking modules or API.

    ```yaml
    >>> earlyStopping:
    >>>   - metric: loss
    ```

    ### value

    The metric value for checking the early stopping condition.

    ```yaml
    >>> earlyStopping:
    >>>   - value: 0.5
    ```

    ### optimization

    The optimization defines the goal or how to measure the performance of the defined metric.

    ```yaml
    >>> earlyStopping:
    >>>   - optimization: maximize
    ```

    ### policy

    A policy allows to defines how to evaluate the metric value against the defined value,
    there are a couple of policies:
     * MedianStopping: Early stopping with median stopping,
         this policy computes running medians across all runs and stops
         those whose best performance is worse than the median of the running runs.
     * DiffStopping: Early stopping with diff factor stopping,
         this policy computes checked runs against the best run and
         stops those whose performance is worse than the best by the factor defined by the user.
     * TruncationStopping: Early stopping with truncation stopping,
         this policy stops a percentage of all running runs at every evaluation.
    """

    _IDENTIFIER = "metric_early_stopping"

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    metric: StrictStr
    value: FloatOrRef
    optimization: Union[StrictFloat, V1Optimization]
    policy: Optional[V1EarlyStoppingPolicy]


class V1FailureEarlyStopping(BaseSchemaModel):
    """Failure early stopping is an early stopping strategy based on statuses of runs that allows
    to terminate a dag, a mapping, or hyperparameter tuning group
    when they reach a certain level of failures.

    If a percentage of the runs in the pipeline fail,
    the pipeline will be marked as failed as well,
    and all pending or running operations will be stopped.

    Args:
        kind: str, should be equal to `failure_early_stopping`
        percent: int (>0, <=99)


    ## YAML usage

    ```yaml
    >>> earlyStopping:
    >>>   - kind: failure_early_stopping
    >>>     percent: 50
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1FailureEarlyStopping
    >>> early_stopping = [V1FailureEarlyStopping(percent=50)]
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools
    that this early stopping is `failure_early_stopping`.

    If you are using the python client to create the early stopping,
    this field is not required and is set by default.

    ```yaml
    >>> earlyStopping:
    >>>   - kind: failure_early_stopping
    ```

    ### percent

    The percentage of failed runs at each evaluation interval,
    should be a value between 1 and 99.

    ```yaml
    >>> earlyStopping:
    >>>   - kind: failure_early_stopping
    >>>     percent: 30
    ```
    """

    _IDENTIFIER = "failure_early_stopping"

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    percent: FloatOrRef
