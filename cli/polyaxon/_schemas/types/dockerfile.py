from typing import Any, Dict, List, Optional, Tuple, Union

from clipped.compact.pydantic import Field, StrictStr, validator
from clipped.config.schema import skip_partial
from clipped.types.docker_image import validate_image
from clipped.types.ref_or_obj import RefField

from polyaxon._schemas.types.base import BaseTypeConfig

POLYAXON_DOCKERFILE_NAME = "Dockerfile"
POLYAXON_DOCKER_WORKDIR = "/code"
POLYAXON_DOCKER_SHELL = "/bin/bash"


class V1DockerfileType(BaseTypeConfig):
    """Dockerfile type.

    This type allows to easily construct a dockerfile without
    the need to clone repo or download a file. It exposes a very simple interface for generating
    a dockerfile to build your container.

    Args:
        image: str
        env: Dict, optional
        path: List[str], optional
        copy: Union[List[str], List[[str, str]], optional
        post_run_copy: Union[List[str], List[[str, str]], optional
        run: List[str], optional
        lang_env: str, optional
        uid: str, optional
        gid: str, optional
        username: str, optional, default 'polyaxon'
        filename: str, optional
        workdir: str, optional
        workdir_path: str, optional
        shell: str, optional

    ### YAML usage

    ### Usage in IO and params definition

    The inputs definition

    ```yaml
    >>> inputs:
    >>>   - name: test1
    >>>     type: dockerfile
    ```

    The params usage

    ```yaml
    >>> params:
    >>>   test1:
    >>>     value:
    >>>       image: test
    >>>       run: ["pip install package1"]
    >>>       env: {'KEY1': 'en_US.UTF-8', 'KEY2':2}
    ```

    ### Usage in initializers

    ```yaml
     ```yaml
    >>> version:  1.1
    >>> kind: component
    >>> run:
    >>>   kind: job
    >>>   init:
    >>>   - dockerfile:
    >>>       image: test
    >>>       run: ["pip install package1"]
    >>>       env: {'KEY1': 'en_US.UTF-8', 'KEY2':2}
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
    >>>         type=types.DOCKERFILE,
    >>>     ),
    >>> ]
    ```

    The params usage

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1Param
    >>> params = {
    >>>     "test1": V1Param(
    >>>         value=types.V1DockerfileType(
    >>>             image="test:version",
    >>>             run=["pip install package1"],
    >>>             env={'KEY1': 'en_US.UTF-8', 'KEY2':2}
    >>>         )
    >>>     ),
    >>> }
    ```

    ### Usage in initializers

    ```python
    >>> from polyaxon.schemas import V1Component, V1Init, V1Job
    >>> from polyaxon.types import V1DockerfileType
    >>> from polyaxon import k8s
    >>> component = V1Component(
    >>>     run=V1Job(
    >>>        init=[
    >>>             V1Init(
    >>>                 dockerfile=V1DockerfileType(
    >>>                     image="test",
    >>>                     run=["pip install package1"],
    >>>                     env={'KEY1': 'en_US.UTF-8', 'KEY2':2},
    >>>                 )
    >>>             ),
    >>>        ],
    >>>        container=k8s.V1Container(...)
    >>>     )
    >>> )
    ```

    ### Fields
      * image: the base image to use, is will exposed as `FROM` command in the dockerfile.
      * env: environment variables dictionary that will be exposed as `ENV` sections.
      * path: list of paths to be added to your `PATH` environment variable.
      * copy: a list a copy commands that will be exposed as list of COPY commands. You can pass a
        Union[List[str], List[[str, str]], if a str is passed it will be placed under the workdir,
        if [str, str] is passed the path will be placed under the second string.
      * postRunCopy: Similar to the copy section,
        the COPY commands will be placed after RUN commands.
        This could be very useful to leverage any cached commands before copying new artifacts.
      * run: a list a run commands that will be exposed as list of RUN commands.
      * langEnv: if passed it will expose these environment variable: ENV LC_ALL, LANG, LANGUAGE
      * uid and gid: will create a new user based on these 2 values.
      * username: an optional name to use for the uid/gid, default is 'polyaxon' user.
      * filename: an optional name for your dockerfile, default is Dockerfile.
        **N.B.** this is not a path, if you need to generate the dockerfile on a custom path,
        you will need to set the path key on the init container definition.
      * workdir: the WORKDIR for your dockerfile, default is `/code`
      * workdirPath: the local workdir to copy to the docker container.
      * shell: shell type environment variable, default `/bin/bash`.

    ### Example

    ```yaml
    >>> image: image:tag
    >>> env:
    >>>   KEY1: value1
    >>>   KEY2: value2
    >>> path:
    >>> - module/add/to/path
    >>> copy:
    >>> - copy/local/requirements.txt
    >>> - [copy/.cache/dir, /destination]
    >>> run:
    >>> - pip install ...
    >>> - mv foo bar
    >>> postRunCopy:
    >>> - copy/local/path
    >>> - [copy/local/path, /path/to/user/in/container]
    >>> langEnv: en_US.UTF-8
    >>> uid: 2222
    >>> gid: 1111
    >>> filename: Dockerfile2
    >>> workdir: ../my-code
    ```
    """

    _IDENTIFIER = "dockerfile"

    image: StrictStr
    env: Optional[Union[Dict[StrictStr, Any], RefField]]
    path: Optional[Union[List[StrictStr], RefField]]
    copy_: Optional[
        Union[
            List[Union[StrictStr, List[StrictStr], Tuple[StrictStr, StrictStr]]],
            RefField,
        ]
    ] = Field(alias="copy")
    post_run_copy: Optional[
        Union[
            List[Union[StrictStr, List[StrictStr], Tuple[StrictStr, StrictStr]]],
            RefField,
        ]
    ] = Field(alias="postRunCopy")
    run: Optional[Union[List[StrictStr], RefField]]
    lang_env: Optional[StrictStr] = Field(alias="langEnv")
    uid: Optional[Union[int, RefField]]
    gid: Optional[Union[int, RefField]]
    username: Optional[StrictStr]
    filename: Optional[StrictStr] = Field(default=POLYAXON_DOCKERFILE_NAME)
    workdir: Optional[StrictStr] = Field(default=POLYAXON_DOCKER_WORKDIR)
    workdir_path: Optional[StrictStr] = Field(alias="workdirPath")
    shell: Optional[StrictStr] = Field(default=POLYAXON_DOCKER_SHELL)

    @validator("image")
    @skip_partial
    def check_image(cls, image):
        validate_image(image)
        return image

    @property
    def image_tag(self):
        if not self.image:
            return None
        tagged_image = self.image.split(":")
        if len(tagged_image) == 1:
            return "latest"
        if len(tagged_image) == 2:
            return "latest" if "/" in tagged_image[-1] else tagged_image[-1]
        if len(tagged_image) == 3:
            return tagged_image[-1]

    def get_filename(self) -> str:
        return self.filename or POLYAXON_DOCKERFILE_NAME
