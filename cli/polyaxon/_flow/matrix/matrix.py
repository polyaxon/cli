from typing import Union
from typing_extensions import Annotated

from clipped.compact.pydantic import Field
from polyaxon._flow.matrix.bayes import V1Bayes
from polyaxon._flow.matrix.grid_search import V1GridSearch
from polyaxon._flow.matrix.hyperband import V1Hyperband
from polyaxon._flow.matrix.iterative import V1Iterative
from polyaxon._flow.matrix.mapping import V1Mapping
from polyaxon._flow.matrix.random_search import V1RandomSearch
from polyaxon._flow.matrix.tpe import V1TPE


V1Matrix = Annotated[
    Union[
        V1Bayes,
        V1GridSearch,
        V1Hyperband,
        V1TPE,
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
    def has_tpe_matrix(self):
        return self.get_matrix_kind() == V1TPE._IDENTIFIER

    @property
    def has_iterative_matrix(self):
        return self.get_matrix_kind() == V1Iterative._IDENTIFIER
