from typing import List, Optional, Union

from clipped.compact.pydantic import StrictStr
from clipped.types.ref_or_obj import RefField

from polyaxon._schemas.types.base import BaseTypeConfig


class V1GitType(BaseTypeConfig):
    """Git type allows you to pass a git repo as a parameter.

    If used as an input type, Polyaxon can resolve several git connections
    and will turn this input type into an initializer with logic to clone
    the repo with support for branches and commits,
    the requested repo will be exposed as a context for your jobs and operations.

    Args:
        url: str, optional.
        revision: str, optional.
        flags: List[str], optional

    ### YAML usage

    ### Usage in IO and params definition

    The inputs definition

    ```yaml
    >>> inputs:
    >>>   - name: test1
    >>>     type: git
    >>>   - name: test2
    >>>     type: git
    ```

    The params usage

    ```yaml
    >>> params:
    >>>   test1: {value: {"url": "https://github.com/tensorflow/models"}}
    >>>   test2: {value: {revision: "branchA"}, connection: "my-git-connection"}
    >>>   test3: {
    >>>     value: {flags: ["--recursive", "-c http.sslVerify=false"]},
    >>>     connection: "my-git-connection",
    >>>   }
    ```

    ### Usage in initializers

    ```yaml
    >>> version:  1.1
    >>> kind: component
    >>> run:
    >>>   kind: job
    >>>   init:
    >>>   - git: {"url": "https://github.com/tensorflow/models"}
    >>>   - git:
    >>>       revision: branchA
    >>>     connection: my-git-connection
    >>>   - git:
    >>>       flags: ["--recursive", "-c http.sslVerify=false"]
    >>>     connection: my-git-connection
    >>>   ...
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
    >>>         type=types.GIT,
    >>>     ),
    >>>     V1IO(
    >>>         name="test2",
    >>>         type=types.GIT,
    >>>     ),
    >>> ]
    ```

    The params usage

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1Param
    >>> params = {
    >>>     "test1": V1Param(
    >>>         value=types.V1GitType(url="https://github.com/tensorflow/models")
    >>>     ),
    >>>     "test2": V1Param(
    >>>         value=types.V1GitType(revision="branchA"),
    >>>         connection="my-git-connection",
    >>>     ),
    >>> }
    ```

    ### Usage in initializers
    ```python
    >>> from polyaxon.schemas import V1Component, V1Init, V1Job
    >>> from polyaxon.types import V1GitType
    >>> from polyaxon import k8s
    >>> component = V1Component(
    >>>     run=V1Job(
    >>>        init=[
    >>>             V1Init(
    >>>               git=V1GitType(url="https://github.com/tensorflow/models"),
    >>>             ),
    >>>             V1Init(
    >>>               git=V1GitType(revision="branchA"),
    >>>               connection="my-git-connection",
    >>>             ),
    >>>        ],
    >>>        container=k8s.V1Container(...)
    >>>     )
    >>> )
    ```
    """

    _IDENTIFIER = "git"

    url: Optional[StrictStr]
    revision: Optional[StrictStr]
    flags: Optional[Union[List[StrictStr], RefField]]

    def get_name(self):
        if self.url:
            return self.url.split("/")[-1].split(".")[0]
        return None
