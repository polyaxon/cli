from typing import Union
from typing_extensions import Annotated

from pydantic import Field

from polyaxon.polyflow.early_stopping.policies import (
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
