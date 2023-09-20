from typing import Union
from typing_extensions import Annotated

from clipped.compact.pydantic import Field

from polyaxon._flow.early_stopping.policies import (
    V1DiffStoppingPolicy,
    V1FailureEarlyStopping,
    V1MedianStoppingPolicy,
    V1MetricEarlyStopping,
    V1TruncationStoppingPolicy,
)

V1EarlyStopping = Annotated[
    Union[V1MetricEarlyStopping, V1FailureEarlyStopping],
    Field(discriminator="kind", alias="earlyStopping"),
]
