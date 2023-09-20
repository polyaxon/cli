from typing import Union
from typing_extensions import Annotated

from clipped.compact.pydantic import Field

from polyaxon._flow.component.component import V1Component
from polyaxon._flow.references import V1DagRef, V1HubRef, V1PathRef, V1UrlRef

V1ComponentReference = Annotated[
    Union[V1Component, V1DagRef, V1HubRef, V1PathRef, V1UrlRef],
    Field(discriminator="kind"),
]
