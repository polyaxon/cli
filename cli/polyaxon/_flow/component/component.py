from typing import List, Optional, Union
from typing_extensions import Literal

from polyaxon._flow.component.base import BaseComponent
from polyaxon._flow.io import V1IO
from polyaxon._flow.references import RefMixin
from polyaxon._flow.run import RunMixin, V1Runtime
from polyaxon._flow.templates import TemplateMixinConfig, V1Template


class V1Component(
    BaseComponent,
    TemplateMixinConfig,
    RunMixin,
    RefMixin,
):
    """Component is a discrete, repeatable, and self-contained action that defines
    an environment and a runtime.

    A component is made of code that performs an action,
    such as container building, data preprocessing, data transformation, model training, and so on.

    You can use any language to write the logic of your component,
    Polyaxon uses containers to execute that logic.

    Components are definitions that can be shared if they reach a
    certain maturity and can be managed by the [Component Hub](/docs/management/component-hub/).
    This allows you to create a library of frequently-used components and reuse them
    either by submitting them directly or by referencing them from your operations.

    Components can be used as well to extract as much information and be used as templates
    with default queues, container resources requirements, node scheduling, ...

    Args:
        version: str
        kind: str, should be equal to `component`
        name: str, optional
        description: str, optional
        tags: List[str], optional
        presets: List[str], optional
        queue: str, optional
        namespace: str, optional
        cache: [V1Cache](/docs/automation/helpers/cache/), optional
        termination: [V1Termination](/docs/core/specification/termination/), optional
        plugins: [V1Plugins](/docs/core/specification/plugins/), optional
        build: [V1Build](/docs/automation/builds/), optional
        hooks: List[[V1Hook](/docs/automation/hooks/)], optional
        inputs: [V1IO](/docs/core/specification/io/), optional
        outputs: [V1IO](/docs/core/specification/io/), optional
        run: Union[[V1Job](/docs/experimentation/jobs/), [V1Service](/docs/experimentation/services/), [V1TFJob](/docs/experimentation/distributed/tf-jobs/), [V1PytorchJob](/docs/experimentation/distributed/pytorch-jobs/), [V1MPIJob](/docs/experimentation/distributed/mpi-jobs/), [V1PaddleJob](/docs/experimentation/distributed/paddle-jobs/), [V1RayJob](/docs/experimentation/distributed/ray-jobs/), [V1DaskJob](/docs/experimentation/distributed/dask-jobs/), [V1Dag](/docs/automation/flow-engine/specification/)]  # noqa
        template: [V1Template](/docs/core/specification/template/), optional

    ## YAML usage

    ```yaml
    >>> component:
    >>>   version: 1.1
    >>>   kind: component
    >>>   name:
    >>>   description:
    >>>   tags:
    >>>   presets:
    >>>   queue:
    >>>   namespace:
    >>>   cache:
    >>>   termination:
    >>>   plugins:
    >>>   actions:
    >>>   hooks:
    >>>   inputs:
    >>>   outputs:
    >>>   build:
    >>>   run:
    >>>   isApproved:
    >>>   template:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import (
    >>>     V1Build, V1Cache, V1Component, V1Hook, V1IO, V1Plugins, V1Termination
    >>> )
    >>> component = V1Component(
    >>>     name="test",
    >>>     description="test",
    >>>     tags=["test"],
    >>>     presets=["test"],
    >>>     queue="test",
    >>>     namespace="test",
    >>>     cache=V1Cache(...),
    >>>     termination=V1Termination(...),
    >>>     plugins=V1Plugins(...),
    >>>     hooks=[V1Hook(...)],
    >>>     inputs=[V1IO(...)],
    >>>     outputs=[V1IO(...)],
    >>>     build=V1Build(...),
    >>>     run=...
    >>> )
    ```

    ## Fields

    ### version

    The polyaxon specification version to use to validate the component.

    If you are using the component inline in an operation, this field is not required since it
    will be populated by the operation.

    ```yaml
    >>> component:
    >>>   version: 1.1
    ```

    ### kind

    The kind signals to the CLI, client, and other tools that this is a component.

    If you are using the component inline in an operation or a dag or
    if you are using the python client to create a component,
    this field is not required and is set by default.

    ```yaml
    >>> component:
    >>>   kind: component
    ```

    ### name

    The default component name.

    This name can be a `slug`, a `slug:tag`, `org/slug`, or `org/slug:slug`.

    This name will be passed as the default value to all operations using this component,
    unless the operations override the name or a `--name`
    is passed as an argument to the cli/client.

    ```yaml
    >>> component:
    >>>   name: test
    ```

    ### description

    The default component description.

    This description will be passed as the default value to all operations using this component,
    unless the operations override the description or a
    `--description` is passed as an argument to the cli/client.

    ```yaml
    >>> component:
    >>>   description: test
    ```

    ### tags

    The default component tags.

    These tags will be passed as the default value to all operations using this component,
    unless the operations override the tags or `--tags` are passed as an argument to the cli/client.

    ```yaml
    >>> component:
    >>>   tags: [test]
    ```

    ### presets

    The default component [presets](/docs/core/scheduling-presets/).

    These presets will be passed as the default value to all operations using this component,
    unless the operations override the presets or `--presets`
    is passed as an argument to the cli/client.

    ```yaml
    >>> component:
    >>>   presets: [test]
    ```

    ### queue

    The default component [queue](/docs/core/scheduling-strategies/queues/).

    This queue will be passed as the default value to all operations using this component,
    unless the operations override the queue or `--queue`
    is passed as an argument to the cli/client.

    ```yaml
    >>> component:
    >>>   queue: agent-name/queue-name
    ```

    If the agent name is not specified, Polyaxon will resolve the name of the queue
    based on the default agent.

    ```yaml
    >>> component:
    >>>   queue: queue-name
    ```

    ### namespace

    > **Note**: Please note that this field is only available in some commercial editions.

    The namespace to use, if not provided, it will default to the agent's namespace.

    ```yaml
    >>> component:
    >>>   namespace: polyaxon
    ```

    ### cache

    The default component [cache](/docs/automation/helpers/cache/).

    This cache definition will be passed as the default value to
    all operations using this component,
    unless the operations override the cache or `--nocache`
    is passed as an argument to the cli/client.

    ```yaml
    >>> component:
    >>>   cache:
    >>>     disable: false
    >>>     ttl: 100
    ```

    ### termination

    The default component [termination](/docs/core/specification/termination/).

    This termination definition will be passed as the default value to
    all operations using this component,
    unless the operations override the termination.

    ```yaml
    >>> component:
    >>>   termination:
    >>>     maxRetries: 2
    ```

    ### plugins

    The default component [plugins](/docs/core/specification/plugins/).

    This plugins definition will be passed as the default value to
    all operations using this component,
    unless the operations override the plugins.

    ```yaml
    >>> component:
    >>>   name: debug
    >>>   ...
    >>>   plugins:
    >>>     auth: false
    >>>     collectLogs: false
    >>>   ...
    ```

    Build using docker:

    ```yaml
    >>> component:
    >>>   name: build
    >>>   ...
    >>>   plugins:
    >>>     docker: true
    >>>   ...
    ```

    ### inputs

    The [inputs](/docs/core/specification/io/) definition for this component.

    If the component defines required inputs, anytime a user tries to run
    this component without passing the required params or passing params with wrong types,
    an exception will be raised.

    ```yaml
    >>> component:
    >>>   name: tensorboard
    >>>   ...
    >>>   inputs:
    >>>     - name: image
    >>>       type: str
    >>>       isOptional: true
    >>>       value: tensorflow:2.1
    >>>     - name: log_dir
    >>>       type: path
    >>>   ...
    ```

    ### outputs

    The [outputs](/docs/core/specification/io/) definition for this component.

    If the component defines required outputs, no exception will be raised at execution time,
    since Polyaxon considers the output values will be resolved in the future,
    for example during the run time when the user will be using the tracking
    client to log a metric or a value or an artifact.

    Sometimes the outputs can be resolved immediately at execution time,
    for example a container image name, because such information is required for the
    job to finish successfully, i.e. pushing the image with the correct name,
    in that case you can disable the `delayValidation` flag.

    ```yaml
    >>> component:
    >>>   name: tensorboard
    >>>   ...
    >>>   outputs:
    >>>     - name: image
    >>>       type: str
    >>>       delayValidation: false
    >>>   ...
    ```

    ### build

    > **Note**: Please check [V1Build](/docs/automation/builds/) for more details.

    This section defines if this component should build a container before starting the main logic.
    If the build section is provided, Polyaxon will set the main operation to a pending state
    until the build is done and then it will use the resulting docker image
    for starting the main container.

    ```yaml
    >>> component:
    >>>   ...
    >>>   build:
    >>>     hubRef: kaniko
    >>>   ...
    ```

    ### run

    This is the section that defines the runtime of the component:
     * [V1Job](/docs/experimentation/jobs/): for running batch jobs, model training experiments,
       data processing jobs, ...
     * [V1Service](/docs/experimentation/services/): for running tensorboards, notebooks,
       streamlit, custom services or an API.
     * [V1TFJob](/docs/experimentation/distributed/tf-jobs/): for running distributed
       Tensorflow training job.
     * [V1PytorchJob](/docs/experimentation/distributed/pytorch-jobs/): for running distributed
       Pytorch training job.
     * [V1MPIJob](/docs/experimentation/distributed/mpi-jobs/): for running distributed MPI job.
     * [V1PaddleJob](/docs/experimentation/distributed/paddle-jobs/): for running distributed
       PaddlePaddle training job.
     * [V1RayJob](/docs/experimentation/distributed/ray-jobs/): for running a ray job.
     * [V1DaskJob](/docs/experimentation/distributed/dask-jobs/): for running a Dask job.
     * [V1Dag](/docs/automation/flow-engine/specification/): for running a DAG/workflow.

    ### isApproved

    This is a flag to trigger human validation before queuing and scheduling this component.
    The default behavior is `True` even when the field is not set, i.e. no validation is required.
    To require a human validation prior to scheduling an operation,
    you can set this field to `False`.

    ```yaml
    >>> isApproved: false
    ```

    ### Cost

    A field to define the cost of running the operation. The value is a float and should map to a
    convention of a cost estimation in your team or
    it can map directly to the cost of using the environment where the operation is running.

    ```yaml
    >>> cost: 2.2
    ```
    """

    _IDENTIFIER = "component"

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    inputs: Optional[List[V1IO]]
    outputs: Optional[List[V1IO]]
    run: Union[V1Runtime]
    template: Optional[V1Template]

    def get_run_kind(self):
        return self.run.kind if self.run else None

    def get_kind_value(self):
        return self.name

    def get_run_dict(self):
        config_dict = self.to_light_dict()
        config_dict.pop("tag", None)
        return config_dict

    def get_name(self):
        return self.name.split(":")[0] if self.name else None
