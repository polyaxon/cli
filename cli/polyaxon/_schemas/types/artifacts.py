from typing import List, Optional, Union

from clipped.compact.pydantic import StrictInt
from clipped.types.ref_or_obj import RefField

from polyaxon._schemas.types.base import BaseTypeConfig


class V1ArtifactsType(BaseTypeConfig):
    """Artifacts type allows to easily pass
    the files and directories to initialize as a single parameter.

    If used as an input type, Polyaxon can resolve several connections (blob storage and volumes)
    and will turn this input type into an initializer with logic to download/provide
    the requested files and/or directories into a context for your jobs and operations.


    Args:
        files: Union[List[str], List[[str, str]], optional,
             list of file subpaths or a list of [path from, path to].
        dirs: Union[List[str], List[[str, str]], optional,
             list of directory subpaths or a list of [path from, path to].

    ### YAML usage

    ### Usage in IO and params definition

    The inputs definition

    ```yaml
    >>> inputs:
    >>>   - name: some-file-names
    >>>     type: artifacts
    >>>   - name: tensorboard-log-dir
    >>>     type: artifacts
    >>>   - name: dataset1
    >>>     type: artifacts
    ```

    The params usage

    ```yaml
    >>> params:
    >>>   some-file-names: {value: {files: ["file1", "/path/to/file2"]}}
    >>>   custom-file-paths: {value: {files: [["file1", "to/this/path/file1"], "/path/to/file2"]}}
    >>>   tensorboard-log-dir: {value: {dirs: ["/tensorboard-logs"]}, connection: "foo", toInit: True}
    >>>   dataset1: {value: {value: {dirs: ["/"]}, connection: "s3-dataset", init: True}
    ```

    The first param will be just a list of files definition that
    the user should know how to handle in their program.

    The second param, Polyaxon will load only that directory path from connection "foo".
    This connection could be any a bucket or a volume.

    In the third param, `dataset1` will be resolved automatically because
    Polyaxon knows about that connection and that it's of type S3.
    It will load all data in that S3 bucket before starting the experiment.

    ### Usage in initializers

    ```yaml
    >>> version:  1.1
    >>> kind: component
    >>> run:
    >>>   kind: job
    >>>   init:
    >>>   - artifacts:
    >>>       files: ["file1", "/path/to/file2"]
    >>>   - artifacts:
    >>>       files: [["file1", "to/this/path/file1"], "/path/to/file2"]
    >>>   - artifacts:
    >>>       dirs: ["/tensorboard-logs"]
    >>>     connection: foo
    >>>   - artifacts:
    >>>       dirs: ["/"]
    >>>     connection: s3-datase
    >>>
    >>>   container:
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
    >>>         name="some-file-names",
    >>>         type=types.ARTIFACTS,
    >>>     ),
    >>>     V1IO(
    >>>         name="tensorboard-log-dir",
    >>>         type=types.ARTIFACTS,
    >>>     ),
    >>>     V1IO(
    >>>         name="dataset1",
    >>>         type=types.ARTIFACTS,
    >>>     )
    >>> ]
    ```

    The params usage

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1Param
    >>> params = {
    >>>     "test1": V1Param(value=types.V1ArtifactsType(files=["file1", "/path/to/file2"])),
    >>>     "test2": V1Param(
    >>>         value=types.V1ArtifactsType(dirs=["/tensorboard-logs"]),
    >>>         connection="foo",
    >>>         to_init=True
    >>>     ),
    >>>     "test3": V1Param(
    >>>         value=types.V1ArtifactsType(dirs=["/"]),
    >>>         connection="s3-dataset",
    >>>         to_init=True
    >>>     ),
    >>> }
    ```

    ### Usage in initializers

    ```python
    >>> from polyaxon.schemas import V1Component, V1Init, V1Job
    >>> from polyaxon.types import V1ArtifactsType
    >>> from polyaxon import k8s
    >>> component = V1Component(
    >>>     run=V1Job(
    >>>        init=[
    >>>             V1Init(
    >>>                 artifacts=V1ArtifactsType(files=["file1", "/path/to/file2"])
    >>>             ),
    >>>             V1Init(
    >>>                 artifacts=V1ArtifactsType(dirs=["/tensorboard-logs"]),
    >>>                 connection="foo"
    >>>             ),
    >>>             V1Init(
    >>>                 artifacts=V1ArtifactsType(dirs=["/"]),
    >>>                 connection="s3-dataset"
    >>>             ),
    >>>        ],
    >>>        container=k8s.V1Container(...)
    >>>     )
    >>> )
    ```
    """

    _IDENTIFIER = "artifacts"

    files: Optional[Union[List[Union[str, List[str]]], RefField]]
    dirs: Optional[Union[List[Union[str, List[str]]], RefField]]
    workers: Optional[Union[StrictInt, RefField]]
