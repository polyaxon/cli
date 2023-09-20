from typing import Union
from typing_extensions import Annotated

from clipped.compact.pydantic import Field

from polyaxon._flow.matrix.bayes import (
    GaussianProcessConfig,
    UtilityFunctionConfig,
    V1Bayes,
)
from polyaxon._flow.matrix.enums import (
    AcquisitionFunctions,
    GaussianProcessesKernels,
    V1HPKind,
    V1MatrixKind,
)
from polyaxon._flow.matrix.grid_search import V1GridSearch
from polyaxon._flow.matrix.hyperband import V1Hyperband
from polyaxon._flow.matrix.hyperopt import V1Hyperopt
from polyaxon._flow.matrix.iterative import V1Iterative
from polyaxon._flow.matrix.mapping import V1Mapping
from polyaxon._flow.matrix.params import (
    V1HpChoice,
    V1HpDateRange,
    V1HpDateTimeRange,
    V1HpGeomSpace,
    V1HpLinSpace,
    V1HpLogNormal,
    V1HpLogSpace,
    V1HpLogUniform,
    V1HpNormal,
    V1HpParam,
    V1HpPChoice,
    V1HpQLogNormal,
    V1HpQLogUniform,
    V1HpQNormal,
    V1HpQUniform,
    V1HpRange,
    V1HpUniform,
    validate_pchoice,
)
from polyaxon._flow.matrix.random_search import V1RandomSearch
from polyaxon._flow.matrix.tuner import V1Tuner

V1Matrix = Annotated[
    Union[
        V1Bayes,
        V1GridSearch,
        V1Hyperband,
        V1Hyperopt,
        V1Iterative,
        V1Mapping,
        V1RandomSearch,
    ],
    Field(discriminator="kind"),
]


class MatrixMixin:
    def get_matrix_kind(self):
        raise NotImplementedError

    @property
    def has_mapping_matrix(self):
        return self.get_matrix_kind() == V1Mapping._IDENTIFIER

    @property
    def has_grid_search_matrix(self):
        return self.get_matrix_kind() == V1GridSearch._IDENTIFIER

    @property
    def has_random_search_matrix(self):
        return self.get_matrix_kind() == V1RandomSearch._IDENTIFIER

    @property
    def has_hyperband_matrix(self):
        return self.get_matrix_kind() == V1Hyperband._IDENTIFIER

    @property
    def has_bo_matrix(self):
        return self.get_matrix_kind() == V1Bayes._IDENTIFIER

    @property
    def has_hyperopt_matrix(self):
        return self.get_matrix_kind() == V1Hyperopt._IDENTIFIER

    @property
    def has_iterative_matrix(self):
        return self.get_matrix_kind() == V1Iterative._IDENTIFIER
