from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.types.ref_or_obj import RefField
from clipped.utils.enums import PEnum
from pydantic import Field, StrictStr, validator

from polyaxon.k8s import k8s_schemas, k8s_validation
from polyaxon.polyflow.run.base import BaseRun
from polyaxon.polyflow.run.kinds import V1RunKind
from polyaxon.polyflow.run.resources import V1RunResources
from polyaxon.polyflow.run.spark.replica import V1SparkReplica


class V1SparkType(str, PEnum):
    JAVA = "java"
    SCALA = "scala"
    PYTHON = "python"
    R = "r"


class V1SparkDeploy(str, PEnum):
    CLUSTER = "cluster"
    CLIENT = "client"
    IN_CLUSTER_CLIENT = "in_cluster_client"


class V1SparkJob(BaseRun):
    """Spark jobs are used to run Spark applications on Kubernetes.

    [Apache Spark](https://spark.apache.org/) is data-processing engine.

    Args:
        kind: str, should be equal `sparkjob`
        connections: List[str], optional
        volumes: List[[Kubernetes Volume](https://kubernetes.io/docs/concepts/storage/volumes/)],
             optional
        type: str [`JAVA`, `SCALA`, `PYTHON`, `R`]
        spark_version: str, optional
        python_version: str, optional
        deploy_mode: str, optional
        main_class: str, optional
        main_application_file: str, optional
        arguments: List[str], optional
        hadoop_conf: Dict[str, str], optional
        spark_conf: Dict[str, str], optional
        hadoop_config_map: str, optional
        spark_config_map: str, optional
        executor: [V1SparkReplica](/docs/experimentation/distributed/spark-replica/)
        driver: [V1SparkReplica](/docs/experimentation/distributed/spark-replica/)

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   connections:
    >>>   volumes:
    >>>   type:
    >>>   sparkVersion:
    >>>   deployMode:
    >>>   mainClass:
    >>>   mainApplicationFile:
    >>>   arguments:
    >>>   hadoopConf:
    >>>   sparkConf:
    >>>   hadoopConfigMap:
    >>>   sparkConfigMap:
    >>>   executor:
    >>>   driver:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.polyflow import V1Environment, V1Init, V1SparkJob, V1SparkReplica, V1SparkType
    >>> from polyaxon.k8s import k8s_schemas
    >>> spark_job = V1SparkJob(
    >>>     connections=["connection-name1"],
    >>>     volumes=[k8s_schemas.V1Volume(...)],
    >>>     type=V1SparkType.PYTHON,
    >>>     spark_version="3.0.0",
    >>>     spark_conf={...},
    >>>     driver=V1SparkReplica(...),
    >>>     executor=V1SparkReplica(...),
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this component's runtime is a job.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    ```

    ### connections

    A list of [connection names](/docs/setup/connections/) to resolve for the job.

    <blockquote class="light">
    If you are referencing a connection it must be configured.
    All referenced connections will be checked:

     * If they are accessible in the context of the project of this run

     * If the user running the operation can have access to those connections
    </blockquote>

    After checks, the connections will be resolved and inject any volumes, secrets, configMaps,
    environment variables for your main container to function correctly.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   connections: [connection1, connection2]
    ```

    ### volumes

    A list of [Kubernetes Volumes](https://kubernetes.io/docs/concepts/storage/volumes/)
    to resolve and mount for your jobs.

    This is an advanced use-case where configuring a connection is not an option.

    When you add a volume you need to mount it manually to your container(s).

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   volumes:
    >>>     - name: volume1
    >>>       persistentVolumeClaim:
    >>>         claimName: pvc1
    >>>   ...
    ```

    ### type

    Tells the type of the Spark application, possible values: `Java`, `Scala`, `Python`, `R`

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   type: Python
    >>>   ...
    ```

    ### sparkVersion

    The version of Spark the application uses.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   sparkVersion: 3.0.0
    >>>   ...
    ```

    ### deployMode

    The deployment mode of the Spark application.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   deployMode: cluster
    >>>   ...
    ```

    ### mainClass

    The fully-qualified main class of the Spark application.
    This only applies to Java/Scala Spark applications.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   mainClass: ...
    >>>   ...
    ```

    ### mainApplicationFile

    The path to a bundled JAR, Python, or R file of the application.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   mainApplicationFile: ...
    >>>   ...
    ```

    ### arguments

    List of arguments to be passed to the application.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   arguments: [...]
    >>>   ...
    ```

    ### hadoopConf

    HadoopConf carries user-specified Hadoop configuration properties as they would use
    the "--conf" option in spark-submit.
    The SparkApplication controller automatically adds prefix "spark.hadoop."
    to Hadoop configuration properties.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   hadoopConf: {...}
    >>>   ...
    ```

    ### sparkConf

    Carries user-specified Spark configuration properties as they would use the  "--conf" option in
    spark-submit.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   sparkConf: {...}
    >>>   ...
    ```

    ### hadoopConfigMap

    Carries the name of the ConfigMap containing Spark configuration files such as log4j.properties.
    The controller will add environment variable SPARK_CONF_DIR to
    the path where the ConfigMap is mounted to.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   hadoopConfigMap: {...}
    >>>   ...
    ```

    ### sparkConfigMap

    Carries the name of the ConfigMap containing Spark configuration files such as log4j.properties.
    The controller will add environment variable SPARK_CONF_DIR to the
    path where the ConfigMap is mounted to.

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   sparkConfigMap: {...}
    >>>   ...
    ```

    ### executor

    Executor is a spark replica specification

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   executor:
    >>>     replicas: 1
    >>>     ...
    >>>   ...
    ```

    ### driver

    Driver a spark replica specification

    ```yaml
    >>> run:
    >>>   kind: sparkjob
    >>>   driver:
    >>>     replicas: 1
    >>>     ...
    >>>   ...
    ```
    """

    _IDENTIFIER = V1RunKind.SPARKJOB
    _SWAGGER_FIELDS = [
        "volumes",
    ]

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    connections: Optional[Union[List[StrictStr], RefField]]
    volumes: Optional[Union[List[k8s_schemas.V1Volume], RefField]]
    type: Optional[V1SparkType]
    spark_version: Optional[StrictStr] = Field(alias="sparkVersion")
    python_version: Optional[StrictStr] = Field(alias="pythonVersion")
    deploy_mode: Optional[V1SparkDeploy] = Field(alias="deployMode")
    main_class: Optional[StrictStr] = Field(alias="mainClass")
    main_application_file: Optional[StrictStr] = Field(alias="mainApplicationFile")
    arguments: Optional[Union[List[StrictStr], RefField]]
    hadoop_conf: Optional[Union[Dict[StrictStr, StrictStr], RefField]] = Field(
        alias="hadoopConf"
    )
    spark_conf: Optional[Union[Dict[StrictStr, StrictStr], RefField]] = Field(
        alias="sparkConf"
    )
    hadoop_config_map: Optional[Union[Dict[StrictStr, StrictStr], RefField]] = Field(
        alias="hadoopConfigMap"
    )
    spark_config_map: Optional[Union[Dict[StrictStr, StrictStr], RefField]] = Field(
        alias="sparkConfigMap"
    )
    executor: Optional[Union[V1SparkReplica, RefField]]
    driver: Optional[Union[V1SparkReplica, RefField]]

    @validator("volumes", always=True, pre=True)
    def validate_volumes(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_volume(vi) for vi in v]

    def get_resources(self):
        resources = V1RunResources()
        for i in range(self.replicas or 1):
            resources += V1RunResources.from_container(self.container)

        return resources

    def get_all_containers(self):
        return [self.container] if self.container else []

    def get_all_connections(self):
        return self.connections or []

    def get_all_init(self):
        return self.init or []
