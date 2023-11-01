from typing import List, Optional, Union

from clipped.compact.pydantic import Field, StrictInt, StrictStr, validator
from clipped.config.constants import PARAM_REGEX
from clipped.types.ref_or_obj import RefField
from clipped.types.uuids import UUIDStr
from clipped.utils.lists import to_list

from polyaxon._schemas.types.base import BaseTypeConfig


class V1TensorboardType(BaseTypeConfig):
    """Tensorboard type.

    This type allows to initialize Tensorboard logs foe one or multiple operations.

    Args:
        port: int
        uuids: List[str]
        use_names: bool, optional
        path_prefix: str, optional
        plugins: List[str]

    ### YAML usage

    ### Usage in IO and params definition

    The inputs definition

    ```yaml
    >>> inputs:
    >>>   - name: tensorboard_content
    >>>     type: tensorboard
    ```

    The params usage

    ```yaml
    >>> params:
    >>>   tensorboard_content:
    >>>     value:
    >>>       port: 6006
    >>>       uuids: "d1410a914d18457589b91926d8c23db4,56f1a7f20f1d4f7f9e1a108b3c6b6031"
    >>>       useNames: true
    ```

    ### Usage in initializers

    ```yaml
     ```yaml
    >>> version:  1.1
    >>> kind: component
    >>> run:
    >>>   kind: service
    >>>   init:
    >>>   - tensorboard:
    >>>       uuids: "{{uuids}}"
    >>>       port: "{{globals.ports[0]}}"
    >>>       pathPrefix: "{{globals.base_url}}"
    >>>       useNames: true
    >>>       plugins: "tensorboard-plugin-profile"
    ```

    ### Python usage

    ### Usage in IO and params definition

    The inputs definition

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1IO
    >>> inputs = [
    >>>     V1IO(
    >>>         name="tensorboard_content",
    >>>         type=types.TENSORBOARD,
    >>>     ),
    >>> ]
    ```

    The params usage

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1Param
    >>>
    >>> params = {
    >>>     "test1": V1Param(
    >>>         value=types.V1TensorboardType(
    >>>             port=6006,
    >>>             uuids="d1410a914d18457589b91926d8c23db4,56f1a7f20f1d4f7f9e1a108b3c6b6031",
    >>>             use_names=True,
    >>>         )
    >>>     ),
    >>> }
    ```

    ### Usage in initializers

    ```python
    >>> from polyaxon.schemas import V1Component, V1Init, V1Job
    >>> from polyaxon.types import V1FileType
    >>> from polyaxon import k8s
    >>> component = V1Component(
    >>>     run=V1Job(
    >>>        init=[
    >>>             V1Init(
    >>>                 file=V1TensorboardType(
    >>>                     uuids="{{uuids}}",
    >>>                     port="{{globals.ports[0]}}",
    >>>                     path_prefix="{{globals.base_url}}",
    >>>                     use_names=True,
    >>>                     plugins="tensorboard-plugin-profile",
    >>>                 )
    >>>             ),
    >>>        ],
    >>>        container=k8s.V1Container(...)
    >>>     )
    >>> )
    ```

    ### Fields
      * port: port to expose the tensorboard service.
      * uuids: comma separated list of operation's uuids to load the tensorboard logs from.
      * useNames: an optional flag to initialize the paths under the operation's names.
      * pathPrefix: an optional path prefix to use for exposing the service.
      * plugins: an optional comma separated list of plugins to install before starting the tensorboard service.
    """

    _IDENTIFIER = "tensorboard"

    port: Optional[Union[StrictInt, RefField]]
    uuids: Optional[Union[List[UUIDStr], RefField]]
    use_names: Optional[Union[bool, RefField]] = Field(alias="useNames")
    path_prefix: Optional[StrictStr] = Field(alias="pathPrefix")
    plugins: Optional[Union[List[StrictStr], RefField]]

    @validator("uuids", "plugins", pre=True)
    def validate_str_list(cls, v, field):
        if isinstance(v, str) and v is not None and not PARAM_REGEX.search(v):
            return to_list(v, check_str=True)
        return v
