from typing import Optional

from clipped.compact.pydantic import Field, StrictStr
from polyaxon._schemas.types.base import BaseTypeConfig


class V1Mount(BaseTypeConfig):
    """Mount specification for mapping local paths to run paths.

    Mounts are used by the CLI to upload local files or directories when
    submitting an operation. A mount can be declared as an object with `from`
    and `to` fields, or as a shorthand string in the form `from:to`. If `to`
    is omitted, the source path is used as the destination.

    Args:
        path_from: str, optional, source path on the local machine.
        path_to: str, optional, destination path in the run context.

    ## YAML usage

    ```yaml
    >>> mount:
    >>>   - from: ./src
    >>>     to: /workspace/src
    >>>   - ./requirements.txt:/workspace/requirements.txt
    >>>   - ./config.yaml
    ```

    ## Python usage

    ```python
    >>> from polyaxon._schemas.types.mounts import V1Mount
    >>> mount = [
    >>>     V1Mount(path_from="./src", path_to="/workspace/src"),
    >>>     V1Mount(path_from="./requirements.txt", path_to="/workspace/requirements.txt"),
    >>> ]
    ```
    """

    _IDENTIFIER = "mount"

    path_from: Optional[StrictStr] = Field(alias="from", default=None)
    path_to: Optional[StrictStr] = Field(alias="to", default=None)
