from typing import List, Optional, Union

from clipped.compact.pydantic import (
    NAME_REGEX,
    Field,
    StrictStr,
    field_validator,
    patter_constr,
    validation_before,
)
from clipped.types.ref_or_obj import BoolOrRef, FloatOrRef, RefField
from clipped.utils.lists import to_list

from polyaxon._flow.builds import V1Build
from polyaxon._flow.cache import V1Cache
from polyaxon._flow.hooks import V1Hook
from polyaxon._flow.plugins import V1Plugins
from polyaxon._flow.termination import V1Termination
from polyaxon._schemas.base import BaseSchemaModel


class BaseComponent(BaseSchemaModel):
    version: Optional[float] = None
    kind: Optional[StrictStr] = None
    name: Optional[Union[patter_constr(pattern=NAME_REGEX), RefField]] = None
    description: Optional[StrictStr] = None
    tags: Optional[List[StrictStr]] = None
    presets: Optional[List[StrictStr]] = None
    queue: Optional[StrictStr] = None
    namespace: Optional[StrictStr] = None
    cache: Optional[Union[V1Cache, RefField]] = None
    termination: Optional[Union[V1Termination, RefField]] = None
    plugins: Optional[Union[V1Plugins, RefField]] = None
    build: Optional[Union[V1Build, RefField]] = None
    hooks: Optional[Union[List[V1Hook], RefField]] = None
    is_approved: Optional[BoolOrRef] = Field(alias="isApproved", default=None)
    cost: Optional[FloatOrRef] = None

    @field_validator("tags", "presets", **validation_before)
    def validate_str_list(cls, v):
        if isinstance(v, str):
            return to_list(v, check_str=True)
        return v
