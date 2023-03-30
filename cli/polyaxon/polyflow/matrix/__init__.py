#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Union
from typing_extensions import Annotated

from pydantic import Field

from polyaxon.polyflow.matrix.bayes import (
    AcquisitionFunctions,
    GaussianProcessConfig,
    GaussianProcessesKernels,
    UtilityFunctionConfig,
    V1Bayes,
)
from polyaxon.polyflow.matrix.grid_search import V1GridSearch
from polyaxon.polyflow.matrix.hyperband import V1Hyperband
from polyaxon.polyflow.matrix.hyperopt import V1Hyperopt
from polyaxon.polyflow.matrix.iterative import V1Iterative
from polyaxon.polyflow.matrix.kinds import V1HPKind, V1MatrixKind
from polyaxon.polyflow.matrix.mapping import V1Mapping
from polyaxon.polyflow.matrix.params import (
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
)
from polyaxon.polyflow.matrix.random_search import V1RandomSearch
from polyaxon.polyflow.matrix.tuner import V1Tuner

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
