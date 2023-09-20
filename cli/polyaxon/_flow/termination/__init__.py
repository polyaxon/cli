from typing import Optional

from clipped.compact.pydantic import Field
from clipped.types.ref_or_obj import IntOrRef

from polyaxon._schemas.base import BaseSchemaModel


class V1Termination(BaseSchemaModel):
    """The termination section allows to define and control when
    to stop an operation and how long to keep its resources on the cluster.

    Args:
        max_retries: int, optional
        ttl: int, optional
        timeout: int, optional

    ## YAML usage

    ```yaml
    >>> termination:
    >>>   maxRetries:
    >>>   ttl:
    >>>   timeout:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Termination
    >>> termination = V1Termination(
    >>>     max_retries=1,
    >>>     ttl=1000,
    >>>     timeout=50
    >>> )
    ```

    ## Fields

    ### maxRetries

    Maximum number of retries when an operation fails.

    This field can be used with
    [restartPolicy](/docs/core/specification/environment/#restartpolicy)
    from the environment section.

    This field is the equivalent of the
    [backoffLimit](https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/).
    Polyaxon exposes a uniform specification and knows how
    to manage and inject this value into the underlying primitive of the runtime,
    i.e. Job, Service, TFJob CRD, RayJob CRD, ...

    ```yaml
    >>> termination:
    >>>   maxRetries: 3
    ```

    ### ttl

    Polyaxon will automatically clean all resources just after they finish and after
    the various helpers finish collecting and archiving information from the cluster,
    such as logs, outputs, ... This ensures that your cluster(s) are kept clean and no resources
    are actively putting pressure on the API server.

    That being said, sometimes users might want to keep the resources after
    they finish for sanity check or debugging.

    The ttl field allows you to leverage the TTL controller provided by some primitives,
    for example the
    [ttlSecondsAfterFinished](https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/#clean-up-finished-jobs-automatically), # noqa
    from the Job controller.
    Polyaxon has helpers for resources that don't have a built-in TTL mechanism, such as services,
    so that you can have a uniform definition for all of your operations.

    ```yaml
    >>> termination:
    >>>   ttl: 1000
    ```


    ### timeout

    Sometimes you might stop an operation after a certain time, timeout lets you define how
    long before Polyaxon decides to stop that operation, this is the equivalent of Kubernetes Jobs
    [activeDeadlineSeconds](https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/#job-termination-and-cleanup)  # noqa
    but you can use this field for all runtimes, for instance you might want to stop a
    tensorboard after 12 hours, this way you don't have to actively look for running tensorboards.
    Timeout is also how you can enforce SLAs (Service Level Agreements),
    if one operation have not succeeded by that timedelta, Polyaxon will stop the operation.
    Timeout can be combined with hooks/notifications to
    notify a user or a system about the details of the failure or stopping the operation.

    ```yaml
    >>> termination:
    >>>   timeout: 1000
    ```
    """

    _IDENTIFIER = "termination"

    max_retries: Optional[IntOrRef] = Field(alias="maxRetries")
    ttl: Optional[IntOrRef]
    timeout: Optional[IntOrRef]
