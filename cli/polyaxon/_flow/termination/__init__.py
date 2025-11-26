from typing import Optional, List

from clipped.compact.pydantic import Field
from clipped.types.ref_or_obj import IntOrRef

from polyaxon._schemas.base import BaseSchemaModel


class V1ActivityProbeHttp(BaseSchemaModel):
    """HTTP-based activity probe configuration for detecting service activity.

    Used with service culling to check for activity by polling an HTTP endpoint.
    Commonly used with Jupyter notebooks to poll the `/api/status` endpoint.

    Args:
        path: str, optional - The HTTP path to poll for activity status
        port: int, optional - The port number where the service is listening

    ## YAML usage

    ```yaml
    >>> probe:
    >>>   http:
    >>>     path: "/api/status"
    >>>     port: 8888
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1ActivityProbeHttp
    >>> probe = V1ActivityProbeHttp(
    >>>     path="/api/status",
    >>>     port=8888
    >>> )
    ```

    ## Fields

    ### path

    The HTTP path to the activity status endpoint. For Jupyter notebooks,
    this is typically `/api/status` which returns information about
    last activity, active kernels, and connections.

    ```yaml
    >>> probe:
    >>>   http:
    >>>     path: "/api/status"
    ```

    ### port

    The port number where the service is listening. For Jupyter notebooks,
    this is typically 8888.

    ```yaml
    >>> probe:
    >>>   http:
    >>>     port: 8888
    ```
    """

    path: Optional[str] = None
    port: Optional[int] = None


class V1ActivityProbeExec(BaseSchemaModel):
    """Command-based activity probe configuration for detecting service activity.

    Used with service culling to check for activity by executing a custom command.
    The command should return exit code 0 if there was activity, or exit code 1 if idle.

    Args:
        command: List[str], optional - The command to execute for checking activity

    ## YAML usage

    ```yaml
    >>> probe:
    >>>   exec:
    >>>     command: ["bash", "-c", "check-activity.sh"]
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1ActivityProbeExec
    >>> probe = V1ActivityProbeExec(
    >>>     command=["bash", "-c", "check-activity.sh"]
    >>> )
    ```

    ## Fields

    ### command

    The command to execute inside the container to check for activity.
    The command should return:
    - Exit code 0: Activity detected (service is active)
    - Exit code 1: No activity detected (service is idle)

    The command is executed directly (not in a shell) unless you explicitly
    invoke a shell as shown in the example.

    ```yaml
    >>> probe:
    >>>   exec:
    >>>     command: ["bash", "-c", "test -f /tmp/activity && exit 0 || exit 1"]
    ```
    """

    command: Optional[List[str]] = None


class V1ActivityProbe(BaseSchemaModel):
    """Activity probe configuration for detecting service activity during culling checks.

    Defines how to check if a service is active or idle. You can use either an HTTP probe
    or an exec command probe. Only one probe type should be specified.

    Args:
        exec: V1ActivityProbeExec, optional - Command-based activity probe
        http: V1ActivityProbeHttp, optional - HTTP-based activity probe

    ## YAML usage

    Using HTTP probe for Jupyter:
    ```yaml
    >>> probe:
    >>>   http:
    >>>     path: "/api/status"
    >>>     port: 8888
    ```

    Using exec probe for custom services:
    ```yaml
    >>> probe:
    >>>   exec:
    >>>     command: ["bash", "-c", "check-activity.sh"]
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1ActivityProbe, V1ActivityProbeHttp
    >>> probe = V1ActivityProbe(
    >>>     http=V1ActivityProbeHttp(
    >>>         path="/api/status",
    >>>         port=8888
    >>>     )
    >>> )
    ```

    ## Fields

    ### exec

    Command-based probe that executes a command to check for activity.
    The command should return exit code 0 for active, 1 for idle.

    ```yaml
    >>> probe:
    >>>   exec:
    >>>     command: ["bash", "-c", "check-activity.sh"]
    ```

    ### http

    HTTP-based probe that polls an endpoint to check for activity.
    Commonly used with Jupyter notebooks to check the `/api/status` endpoint.

    ```yaml
    >>> probe:
    >>>   http:
    >>>     path: "/api/status"
    >>>     port: 8888
    ```
    """

    var_exec: Optional[V1ActivityProbeExec] = Field(None, alias="exec")
    http: Optional[V1ActivityProbeHttp] = None


class V1Culling(BaseSchemaModel):
    """Culling configuration for automatically stopping idle services.

    Defines idle-based termination for long-running services like Jupyter notebooks
    or Tensorboard. Unlike absolute timeout which terminates after a fixed duration,
    culling only triggers when the service has been idle for the specified period.

    Args:
        timeout: int, optional - Idle timeout in seconds before culling

    ## YAML usage

    ```yaml
    >>> termination:
    >>>   culling:
    >>>     timeout: 3600  # 1 hour
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Culling
    >>> culling = V1Culling(timeout=3600)
    ```

    ## Fields

    ### timeout

    The duration in seconds that the service needs to be idle before it is culled.
    This works in conjunction with an activity probe to detect when the service
    is idle vs. active.

    Common values:
    - 3600: 1 hour
    - 7200: 2 hours
    - 14400: 4 hours
    - 86400: 24 hours

    ```yaml
    >>> termination:
    >>>   culling:
    >>>     timeout: 3600
    ```

    When combined with an activity probe, the service will be stopped after being
    idle for this duration. The probe determines what "idle" means for your service.
    """

    timeout: Optional[int] = None


class V1Termination(BaseSchemaModel):
    """The termination section allows to define and control when
    to stop an operation and how long to keep its resources on the cluster.

    Args:
        max_retries: int, optional
        ttl: int, optional
        timeout: int, optional
        culling: V1Culling, optional
        probe: V1ActivityProbe, optional

    ## YAML usage

    ```yaml
    >>> termination:
    >>>   maxRetries:
    >>>   ttl:
    >>>   timeout:
    >>>   culling:
    >>>     timeout: 3600
    >>>   probe:
    >>>     http:
    >>>       path: "/api/status"
    >>>       port: 8888
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Termination, V1Culling, V1ActivityProbe, V1ActivityProbeHttp
    >>> termination = V1Termination(
    >>>     max_retries=1,
    >>>     ttl=1000,
    >>>     timeout=50,
    >>>     culling=V1Culling(timeout=3600),
    >>>     probe=V1ActivityProbe(
    >>>         http=V1ActivityProbeHttp(path="/api/status", port=8888)
    >>>     )
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
    i.e. Job, Service, TFJob CRD, RayCluster CRD, ...

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

    ### culling

    > **Note**: Available from v2.12

    Idle-based termination configuration for long-running services. Unlike the absolute `timeout`
    which stops a service after a fixed duration, culling only triggers when the service has been
    idle for the specified period. This is particularly useful for services like Jupyter notebooks
    that may run for long periods but are only actively used occasionally.

    Culling requires an activity probe (see `probe` field) to determine when the service is idle.

    ```yaml
    >>> termination:
    >>>   culling:
    >>>     timeout: 3600  # Stop after 1 hour of idle time
    ```

    You can combine both `timeout` and `culling`. The service will be stopped when either
    condition is met (whichever happens first):

    ```yaml
    >>> termination:
    >>>   timeout: 86400   # Absolute: stop after 24 hours
    >>>   culling:
    >>>     timeout: 3600  # Idle: stop after 1 hour of inactivity
    >>>   probe:
    >>>     http:
    >>>       path: "/api/status"
    >>>       port: 8888
    ```

    ### probe

    > **Note**: Available from v2.12

    Activity probe configuration that defines how to check if a service is active or idle.
    This is used in conjunction with the `culling` field to implement idle-based termination.

    Two probe types are supported:

    **HTTP probe** - Polls an HTTP endpoint to check for activity (recommended for Jupyter):
    ```yaml
    >>> termination:
    >>>   probe:
    >>>     http:
    >>>       path: "/api/status"
    >>>       port: 8888
    ```

    **Exec probe** - Runs a custom command to check for activity:
    ```yaml
    >>> termination:
    >>>   probe:
    >>>     exec:
    >>>       command: ["bash", "-c", "check-activity.sh"]
    ```

    The probe is periodically executed to determine if the service is active.
    For HTTP probes, the endpoint should return activity information.
    For exec probes, the command should exit with code 0 for active, 1 for idle.

    See [services timeout preset documentation](/docs/core/scheduling-presets/services-timeout/)
    for detailed examples and use cases.
    """

    _IDENTIFIER = "termination"

    max_retries: Optional[IntOrRef] = Field(alias="maxRetries", default=None)
    ttl: Optional[IntOrRef] = None
    timeout: Optional[IntOrRef] = None
    culling: Optional[V1Culling] = None
    probe: Optional[V1ActivityProbe] = None
