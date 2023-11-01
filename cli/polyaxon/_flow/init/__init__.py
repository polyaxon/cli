from typing import List, Optional, Union

from clipped.compact.pydantic import Field, StrictStr, root_validator, validator
from clipped.config.schema import skip_partial
from clipped.types.ref_or_obj import RefField

from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon._schemas.types import (
    V1ArtifactsType,
    V1DockerfileType,
    V1FileType,
    V1GitType,
    V1TensorboardType,
)


class V1Init(BaseSchemaModel):
    """Polyaxon init section exposes an interface for users to run init
    containers before the main container containing the logic for training models
    or processing data.

    Polyaxon init section is an extension of
    [Kubernetes init containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/).  # noqa

    Polyaxon init section has special handlers for several connections in addition to the possibility for the users to
    provide their own containers and run any custom init containers which can contain utilities
    or setup scripts not present in the main container.

    By default, all built-in handlers will mount and initialize data under the path
    `/plx-context/artifacts/{{connection-name}}` unless the user passes a custom `path`.

    Args:
        paths: Union[List[str], List[[str, str]], optional,
             list of subpaths or a list of [path from, path to].
        artifacts: [V1ArtifactsType](/docs/core/specification/types/#v1artifactstype), optional
        git: [V1GitType](/docs/core/specification/types/#v1gittype), optional
        dockerfile: [V1DockerfileType](/docs/core/specification/types/#v1dockerfiletype), optional
        file: [V1FileType](/docs/core/specification/types/#v1Filetype), optional
        tensorboard: [V1TensorboardType](/docs/core/specification/types/#v1Tensorboardtype), optional
        lineage_ref: str, optional
        model_ref: str, optional
        artifact_ref: str, optional
        connection: str, optional
        path: str, optional
        container: [Kubernetes Container](https://kubernetes.io/docs/concepts/containers/), optional


    ## YAML usage

    You can only use one of the possibilities for built-in handlers,
    otherwise an exception will be raised.
    It's possible to customize the container used with the default built-in handlers.

    ```yaml
    >>> version:  1.1
    >>> kind: component
    >>> run:
    >>>   kind: job
    >>>   init:
    >>>   - artifacts:
    >>>       dirs: ["path/on/the/default/artifacts/store"]
    >>>   - lineageRef: "281081ab11794df0867e80d6ff20f960:artifactLineageRef"
    >>>   - artifactRef: "artifactVersion"
    >>>   - artifactRef: "otherProjectName:version"
    >>>   - modelRef: "modelVersion"
    >>>   - modelRef: "otherProjectName:version"
    >>>   - connection: gcs-large-datasets
    >>>     artifacts:
    >>>       dirs: ["data"]
    >>>     container:
    >>>       resources:
    >>>         requests:
    >>>           memory: "256Mi"
    >>>           cpu: "500m"
    >>>   - connection: s3-datasets
    >>>     path: "/s3-path"
    >>>     artifacts:
    >>>       files: ["data1", "path/to/data2"]
    >>>   - connection: repo1
    >>>   - git:
    >>>       revision: branch2
    >>>     connection: repo2
    >>>   - dockerfile:
    >>>       image: test
    >>>       run: ["pip install package1"]
    >>>       env: {'KEY1': 'en_US.UTF-8', 'KEY2':2}
    >>>   - file:
    >>>       name: script.sh
    >>>       chmod: "+x"
    >>>       content: |
    >>>         echo test
    >>>   - container:
    >>>       name: myapp-container
    >>>       image: busybox:1.28
    >>>       command: ['sh', '-c', 'echo custom init container']
    >>>
    >>>   container:
    >>>     ...
    ```

    ## Python usage

    Similar to the YAML example if you pass more than one handler, an exception will be raised.
    It's possible to customize the container used with the default built-in handlers.

    ```python
    >>> from polyaxon.schemas import V1Component, V1Init, V1Job
    >>> from polyaxon.types import V1ArtifactsType, V1DockerfileType, V1GitType
    >>> from polyaxon import k8s
    >>> component = V1Component(
    >>>     run=V1Job(
    >>>        init=[
    >>>             V1Init(
    >>>                 artifacts=V1ArtifactsType(dirs=["path/on/the/default/artifacts/store"])
    >>>             ),
    >>>             V1Init(
    >>>                 lineage_ref="281081ab11794df0867e80d6ff20f960:artifactLineageRef"
    >>>             ),
    >>>             V1Init(
    >>>                 artifact_ref="artifactVersion"
    >>>             ),
    >>>             V1Init(
    >>>                 artifact_ref="otherProjectName:version"
    >>>             ),
    >>>             V1Init(
    >>>                 model_ref="modelVersion"
    >>>             ),
    >>>             V1Init(
    >>>                 model_ref="otherProjectName:version"
    >>>             ),
    >>>             V1Init(
    >>>                 connection="gcs-large-datasets",
    >>>                 artifacts=V1ArtifactsType(dirs=["data"]),
    >>>                 container=k8s.V1Container(
    >>>                     resources=k8s.V1ResourceRequirements(requests={"memory": "256Mi", "cpu": "500m"}), # noqa
    >>>                 )
    >>>             ),
    >>>             V1Init(
    >>>               path="/s3-path",
    >>>               connection="s3-datasets",
    >>>                 artifacts=V1ArtifactsType(files=["data1", "path/to/data2"])
    >>>             ),
    >>>             V1Init(
    >>>               connection="repo1",
    >>>             ),
    >>>             V1Init(
    >>>               connection="repo2",
    >>>               git=V1GitType(revision="branch2")
    >>>             ),
    >>>             V1Init(
    >>>                 dockerfile=V1DockerfileType(
    >>>                     image="test",
    >>>                     run=["pip install package1"],
    >>>                     env={'KEY1': 'en_US.UTF-8', 'KEY2':2},
    >>>                 )
    >>>             ),
    >>>             V1Init(
    >>>                 dockerfile=V1FileType(
    >>>                     name="test.sh",
    >>>                     content="echo test",
    >>>                     chmod="+x",
    >>>                 )
    >>>             ),
    >>>             V1Init(
    >>>                 container=k8s.V1Container(
    >>>                     name="myapp-container",
    >>>                     image="busybox:1.28",
    >>>                     command=['sh', '-c', 'echo custom init container']
    >>>                 )
    >>>             ),
    >>>        ],
    >>>        container=k8s.V1Container(...)
    >>>     )
    >>> )
    ```

    ## Understanding init section

    In both the YAML and Python example we are telling Polyaxon to initialize:
     * A directory `path/on/the/default/artifacts/store` from the default `artfactsStore`,
       because we did not specify a connection and we invoked an artifacts handler.
     * An artifact lineage reference based on the run generating the artifact and its lineage name.
     * Two model versions, one version from the same project
       and a second a version from a different project.
       (it's possible to provide the FQN `org_name/model_name:version`)
    * Two artifact versions, one version from the same project
       and a second a version from a different project.
       (it's possible to provide the FQN `org_name/model_name:version`)
     * A directory `data` from a GCS connection named `gcs-large-datasets`, we also
       customized the built-in init container with a new resources section.
     * Two files `data1`, `path/to/data2` from an S3 connection named `s3-datasets`,
       and we specified that the 2 files should be initialized under
       `/s3-path` instead of the default path that Polyaxon uses.
     * A repo configured under the connection name `repo1` will be cloned from the default branch.
     * A repo configured under the connection name `repo2` will be cloned
       from the branch name `branch2`.
     * A dockerfile will be generated with the specification that was provided.
     * A custom container will finally run our own custom code, in this case an echo command.
    """

    _IDENTIFIER = "init"
    _SWAGGER_FIELDS = ["container"]

    artifacts: Optional[Union[V1ArtifactsType, RefField]]
    paths: Optional[Union[List[Union[List[StrictStr], StrictStr]], StrictStr, RefField]]
    git: Optional[Union[V1GitType, RefField]]
    dockerfile: Optional[Union[V1DockerfileType, RefField]]
    file: Optional[Union[V1FileType, RefField]]
    tensorboard: Optional[Union[V1TensorboardType, RefField]]
    lineage_ref: Optional[Union[StrictStr, RefField]] = Field(alias="lineageRef")
    model_ref: Optional[Union[StrictStr, RefField]] = Field(alias="modelRef")
    artifact_ref: Optional[Union[StrictStr, RefField]] = Field(alias="artifactRef")
    connection: Optional[StrictStr]
    path: Optional[StrictStr]
    container: Optional[Union[k8s_schemas.V1Container, RefField]]

    @root_validator
    @skip_partial
    def validate_init(cls, values):
        artifacts = values.get("artifacts")
        paths = values.get("paths")
        git = values.get("git")
        dockerfile = values.get("dockerfile")
        file = values.get("file")
        tensorboard = values.get("tensorboard")
        lineage_ref = values.get("lineage_ref")
        model_ref = values.get("model_ref")
        artifact_ref = values.get("artifact_ref")
        connection = values.get("connection")
        schemas = 0
        if artifacts:
            schemas += 1
        if paths:
            schemas += 1
        if git:
            schemas += 1
        if dockerfile:
            schemas += 1
        if file:
            schemas += 1
        if tensorboard:
            schemas += 1
        if lineage_ref:
            schemas += 1
        if model_ref:
            schemas += 1
        if artifact_ref:
            schemas += 1
        if schemas > 1:
            raise ValueError(
                "Only one of artifacts, paths, git, file, or dockerfile can be set"
            )

        if not connection and git and not git.url:
            raise ValueError(
                "git field without a valid url requires a connection to be passed."
            )
        return values

    @validator("container", always=True, pre=True)
    def validate_container(cls, v):
        return k8s_validation.validate_k8s_container(v)

    def has_connection(self):
        return any(
            [
                self.connection,
                self.git,
                self.dockerfile,
                self.tensorboard,
                self.file,
                self.artifacts,
                self.paths,
            ]
        )
