from typing import List, Optional, Union

from clipped.compact.pydantic import Field, StrictStr, constr, validator
from clipped.types.ref_or_obj import BoolOrRef, FloatOrRef, RefField
from clipped.utils.lists import to_list

from polyaxon._flow.builds import V1Build
from polyaxon._flow.cache import V1Cache
from polyaxon._flow.hooks import V1Hook
from polyaxon._flow.plugins import V1Plugins
from polyaxon._flow.termination import V1Termination
from polyaxon._schemas.base import NAME_REGEX, BaseSchemaModel


class BaseComponent(BaseSchemaModel):
    version: Optional[float]
    kind: Optional[StrictStr]
    name: Optional[Union[constr(regex=NAME_REGEX), RefField]]
    description: Optional[StrictStr]
    tags: Optional[List[StrictStr]]
    presets: Optional[List[StrictStr]]
    queue: Optional[StrictStr]
    namespace: Optional[StrictStr]
    cache: Optional[Union[V1Cache, RefField]]
    termination: Optional[Union[V1Termination, RefField]]
    plugins: Optional[Union[V1Plugins, RefField]]
    build: Optional[Union[V1Build, RefField]]
    hooks: Optional[Union[List[V1Hook], RefField]]
    is_approved: Optional[BoolOrRef] = Field(alias="isApproved")
    cost: Optional[FloatOrRef]

    @validator("tags", "presets", pre=True)
    def validate_str_list(cls, v):
        if isinstance(v, str):
            return to_list(v, check_str=True)
        return v
