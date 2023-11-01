from typing import Optional, Union

from clipped.compact.pydantic import StrictStr
from clipped.types.ref_or_obj import RefField

from polyaxon._schemas.types.base import BaseTypeConfig
from traceml.artifacts import V1ArtifactKind


class V1FileType(BaseTypeConfig):
    """File type.

    This type allows to easily construct a file content without
    the need to clone repo or download a from an external localtion.
    It exposes a very simple interface for generating a file or a script
    that can be used by your containers.

    Args:
        content: str
        filename: str, optional
        kind: str, optional
        chmod: str, optional

    ### YAML usage

    ### Usage in IO and params definition

    The inputs definition

    ```yaml
    >>> inputs:
    >>>   - name: test1
    >>>     type: file
    >>>   - name: test2
    >>>     type: file
    ```

    The params usage

    ```yaml
    >>> params:
    >>>   test1:
    >>>     value:
    >>>       filename: script.sh
    >>>       chmod: +x
    >>>       content: |
    >>>         #!/usr/bin/env bash
    >>>
    >>>         echo 'This is a test.' | wc -w
    >>>   test2:
    >>>     value:
    >>>       filename: script.py
    >>>       content: |
    >>>         print("hello world")
    >>>
    ```

    ### Usage in initializers

    ```yaml
     ```yaml
    >>> version:  1.1
    >>> kind: component
    >>> run:
    >>>   kind: job
    >>>   init:
    >>>   - file:
    >>>       filename: script.sh
    >>>       chmod: +x
    >>>       content: |
    >>>         #!/usr/bin/env bash
    >>>
    >>>         echo 'This is a test.' | wc -w
    >>>   - file:
    >>>       filename: script.py
    >>>       content: |
    >>>         print("hello world")
    >>>     ...
    ```

    ### Python usage

    ### Usage in IO and params definition

    The inputs definition

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1IO
    >>> inputs = [
    >>>     V1IO(
    >>>         name="test1",
    >>>         type=types.FILE,
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
    >>>         value=types.V1FileType(
    >>>             filename="script.sh",
    >>>             chmod="+x",
    >>>             content="#!/usr/bin/env bash\necho 'This is a test.' | wc -w",
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
    >>>                 file=V1FileType(
    >>>                     filename="script.sh",
    >>>                     chmod="+x",
    >>>                     content="#!/usr/bin/env bash\necho 'This is a test.' | wc -w",
    >>>                 )
    >>>             ),
    >>>        ],
    >>>        container=k8s.V1Container(...)
    >>>     )
    >>> )
    ```

    ### Fields
      * filename: an optional filename.
      * content: the content of the file or script.
      * chmod: Custom permission for the generated file.
      * kind: artifact kind, default to `file`.
    """

    _IDENTIFIER = "file"

    kind: Optional[Union[V1ArtifactKind, RefField]]
    content: StrictStr
    filename: Optional[StrictStr]
    chmod: Optional[StrictStr]
