from copy import copy
from typing import Dict, Optional
from typing_extensions import Literal

from clipped.compact.pydantic import Field, StrictStr, root_validator, validator
from clipped.config.patch_strategy import PatchStrategy
from clipped.config.schema import skip_partial, to_partial

from polyaxon._flow.builds import V1Build
from polyaxon._flow.component.component import V1Component
from polyaxon._flow.hooks import V1Hook
from polyaxon._flow.operations.base import BaseOp
from polyaxon._flow.params import V1Param
from polyaxon._flow.references import V1DagRef, V1HubRef, V1PathRef, V1UrlRef
from polyaxon._flow.run.patch import validate_run_patch
from polyaxon._flow.templates import TemplateMixinConfig, V1Template


class V1Operation(BaseOp, TemplateMixinConfig):
    """An operation is how Polyaxon executes a component by passing parameters,
    connections, and a run environment.

    With an operation users can:
     * Pass the parameters for required inputs or override the default values of optional inputs.
     * Patch the definition of the component to set environments, initializers, and resources.
     * Set termination logic and retries.
     * Set trigger logic to start a component in a pipeline context.
     * Parallelize or map the component over a matrix of parameters.
     * Put an operation on a schedule.
     * Subscribe a component to events to trigger executions automatically.

    After resolution and compilation, Polyaxon will prepare an executable
    that will be scheduled on Kubernetes:

    ![polyaxonfile operation](../../../../content/images/references/specification/operation.png)

    Args:
        version: str
        kind: str, should be equal to `operation`
        patch_strategy: str, optional, defaults to post_merge
        is_preset: bool, optional
        is_approved: bool, optional
        name: str, optional
        description: str, optional
        tags: List[str], optional
        presets: str, optional
        queue: str, optional
        namespace: str, optional
        cache: [V1Cache](/docs/automation/helpers/cache/), optional
        termination: [V1Termination](/docs/core/specification/termination/), optional
        plugins: [V1Plugins](/docs/core/specification/plugins/), optional
        params: Dict[str, [V1Param](/docs/core/specification/params/)], optional
        schedule: Union[[V1CronSchedule](/docs/automation/schedules/cron/), [V1IntervalSchedule](/docs/automation/schedules/interval/), [V1DateTimeSchedule](/docs/automation/schedules/datetime/)], optional  # noqa
        events: List[[V1EventTrigger](/docs/automation/events/)], optional
        build: [V1Build](/docs/automation/builds/), optional
        hooks: List[[V1Hook](/docs/automation/hooks/)], optional
        matrix: Union[[V1Mapping](/docs/automation/mapping/), [V1GridSearch](/docs/automation/optimization-engine/grid-search/), [V1RandomSearch](/docs/automation/optimization-engine/random-search/), [V1Hyperband](/docs/automation/optimization-engine/hyperband/), [V1Bayes](/docs/automation/optimization-engine/bayesian-optimization/), [V1Hyperopt](/docs/automation/optimization-engine/hyperopt/), [V1Iterative](/docs/automation/optimization-engine/iterative/)], optional  # noqa
        joins: List[[V1Join](/docs/automation/joins/)], optional
        dependencies: [dependencies](/docs/automation/flow-engine/flow-dependencies/#dependencies), optional  # noqa
        trigger: [trigger](/docs/automation/flow-engine/flow-dependencies/#trigger), optional
        conditions: [conditions](/docs/core/scheduling-strategies/conditional-scheduling/#conditional-scheduling), optional  # noqa
        skip_on_upstream_skip: [skip_on_upstream_skip](/docs/automation/flow-engine/flow-dependencies/#skiponupstreamskip), optional  # noqa
        run_patch: Dict, optional
        hub_ref: str, optional
        dag_ref: str, optional
        url_ref: str, optional
        path_ref: str, optional
        component: [V1Component](/docs/core/specification/component/), optional
        template: [V1Template](/docs/core/specification/template/), optional

    ## YAML usage

    ```yaml
    >>> operation:
    >>>   version: 1.1
    >>>   kind: operation
    >>>   patchStrategy:
    >>>   isPreset:
    >>>   isApproved:
    >>>   name:
    >>>   description:
    >>>   tags:
    >>>   presets:
    >>>   queue:
    >>>   namespace:
    >>>   cache:
    >>>   termination:
    >>>   plugins:
    >>>   events:
    >>>   actions:
    >>>   hooks:
    >>>   params:
    >>>   build:
    >>>   runPatch:
    >>>   hubRef:
    >>>   dagRef:
    >>>   pathRef:
    >>>   component:
    >>>   template:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import (
    >>>     V1Build, V1Cache, V1Component, V1Hook, V1Param, V1Plugins, V1Operation, V1Termination
    >>> )
    >>> from polyaxon.schemas import V1PatchStrategy
    >>> operation = V1Operation(
    >>>     patch_strategy=V1PatchStrategy.REPLACE,
    >>>     name="test",
    >>>     description="test",
    >>>     tags=["test"],
    >>>     presets=["test"],
    >>>     queue="test",
    >>>     namespace="test",
    >>>     cache=V1Cache(...),
    >>>     termination=V1Termination(...),
    >>>     plugins=V1Plugins(...),
    >>>     events=["event-ref1", "event-ref2"],
    >>>     hooks=[V1Hook(...)],
    >>>     outputs={"param1": V1Param(...), ...},
    >>>     build=V1Build(...),
    >>>     component=V1Component(...),
    >>> )
    ```

    ## Fields

    ### version

    The polyaxon specification version to use to validate the operation.

    ```yaml
    >>> operation:
    >>>   version: 1.1
    ```

    ### kind

    The kind signals to the CLI, client, and other tools that this is an operation.

    If you are using the python client to create an operation,
    this field is not required and is set by default.

    ```yaml
    >>> operation:
    >>>   kind: component
    ```

    ### patchStrategy

    Defines how the compiler should handle keys that are defined on the component,
    or how to merge multiple presets when using the override behavior `-f`.

    There are four strategies:
     * `replace`: replaces all keys with new values if provided.
     * `isnull`: only applies new values if the keys have empty/None values.
     * `post_merge`: applies deep merge where newer values are applied last.
     * `pre_merge`: applies deep merge where newer values are applied first.

    ### isPreset

    This is a flag to tell if this operation must be validated or
    is only a preset that will be used with the override behavior to inject extra information
    to the main operation specification.

    For instance a user might want to define a scheduling
    behavior that applies to several operations.
    One way to do that is to set the environment section on every operation.
    But sometimes the same scheduling behavior makes sense for several operations and components.
    In that case, the user can define an operation preset to extract that logic:

    ```yaml
    >>> isPreset: true
    >>> runPatch:
    >>>   environment:
    >>>     nodeSelector:
    >>>       node_label: node_value
    ```

    and use the override behavior to inject that section dynamically:

    ```bash
    polyaxon run -f component -f scheduling-preset.yaml
    ```

    > **Note**: Please check this
    > [in-depth section about presets](/docs/core/scheduling-presets/).

    ### name

    The name to use for this operation run,
    if provided, it will override the component's name otherwise
    the name of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   name: test
    ```

    ### description

    The description to use for this operation run,
    if provided, it will override the component's description otherwise
    the description of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   description: test
    ```

    ### tags

    The tags to use for this operation run,
    if provided, it will override the component's tags otherwise
    the tags of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   tags: [test]
    ```

    ### presets

    The [presets](/docs/management/organizations/presets/) to use for this operation run,
    if provided, it will override the component's presets otherwise
    the presets of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   presets: [test]
    ```

    ### queue

    The [queue](/docs/core/scheduling-strategies/queues/) to use for this operation run,
    if provided, it will override the component's queue otherwise
    the queue of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   queue: agent-name/queue-name
    ```

    If the agent name is not specified, Polyaxon will resolve the name of the queue
    based on the default agent.

    ```yaml
    >>> operation:
    >>>   queue: queue-name
    ```

    ### namespace

    > **Note**: Please note that this field is only available in some commercial editions.

    The namespace to use for this operation run,
    if provided, it will override the component's namespace otherwise
    the namesace of the component will be used if it exists or
    it will default to the agent's namespace.

    ```yaml
    >>> operation:
    >>>   namespace: polyaxon
    ```

    ### cache

    The [cache](/docs/automation/helpers/cache/) to use for this operation run,
    if provided, it will override the component's cache otherwise
    the cache of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   cache:
    >>>     disable: false
    >>>     ttl: 100
    ```

    ### termination

    The [termination](/docs/core/specification/termination/) to use for this operation run,
    if provided, it will override the component's termination otherwise
    the termination of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   termination:
    >>>     maxRetries: 2
    ```

    ### plugins

    The [plugins](/docs/core/specification/plugins/) to use for this operation run,
    if provided, it will override the component's plugins otherwise
    the plugins of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   name: debug
    >>>   ...
    >>>   plugins:
    >>>     auth: false
    >>>     collectLogs: false
    >>>   ...
    ```

    ### params

    The [params](/docs/core/specification/params/)  to pass to the component,
    they will be validated against the inputs/outputs.
    If a parameter is passed and the component does not define a corresponding inputs/outputs,
    a validation error will be raised unless the param has the `contextOnly` flag enabled.

    ```yaml
    >>> operation:
    >>>   params:
    >>>     param1: {value: 1.1}
    >>>     param2: {value: test}
    >>>     param3: {ref: ops.upstream-operation, value: outputs.metric}
    >>>   ...
    ```

    ### build

    > **Note**: Please check [V1Build](/docs/automation/builds/) for more details.

    This section defines if this operation should build a container before starting the main logic.
    If the build section is provided, Polyaxon will set the main operation to a pending state
    until the build is done and then it will use the resulting docker image
    for starting the main container.

    ```yaml
    >>> operation:
    >>>   ...
    >>>   build:
    >>>     hubRef: kaniko
    >>>   ...
    ```

    ### runPatch

    The run patch provides a way to override information about the component's run section,
    for example the container's resources or the environment section.

    The run patch is a dictionary that can modify most of the runtime information and
    will be resolved against the corresponding run kind:

     * [V1Job](/docs/experimentation/jobs/): for running batch jobs, model training experiments, data processing jobs, ...  # noqa
     * [V1Service](/docs/experimentation/services/): for running tensorboards, notebooks, streamlit, custom services or an API.  # noqa
     * [V1TFJob](/docs/experimentation/distributed/tf-jobs/): for running distributed Tensorflow training job.  # noqa
     * [V1PytorchJob](/docs/experimentation/distributed/pytorch-jobs/): for running distributed Pytorch training job.  # noqa
     * [V1PaddleJob](/docs/experimentation/distributed/paddle-jobs/): for running distributed PaddlePaddle training job.  # noqa
     * [V1MXJob](/docs/experimentation/distributed/mx-jobs/): for running distributed MXNet training job.  # noqa
     * [V1XGBoostJob](/docs/experimentation/distributed/xgboost-jobs/): for running distributed XGBoost training job.  # noqa
     * [V1MPIJob](/docs/experimentation/distributed/mpi-jobs/): for running distributed MPI job.  # noqa
     * [V1RayJob](/docs/experimentation/distributed/ray-jobs/): for running a Ray job.
     * [V1DaskJob](/docs/experimentation/distributed/dask-jobs/): for running a Dask job.
     * [V1Dag](/docs/automation/flow-engine/specification/): for running a DAG/workflow.

    For example, if we define a generic component for running Jupyter Notebook:

    ```yaml
    >>> version: 1.1
    >>> kind: component
    >>> name: notebook
    >>> run:
    >>>   kind: service
    >>>   ports: [8888]
    >>>   container:
    >>>     image: "jupyter/tensorflow-notebook"
    >>>     command: ["jupyter", "lab"]
    >>>     args: [
    >>>       "--no-browser",
    >>>       "--ip=0.0.0.0",
    >>>       "--port={{globals.ports[0]}}",
    >>>       "--allow-root",
    >>>       "--NotebookApp.allow_origin=*",
    >>>       "--NotebookApp.trust_xheaders=True",
    >>>       "--NotebookApp.token=",
    >>>       "--NotebookApp.base_url={{globals.base_url}}",
    >>>       "--LabApp.base_url={{globals.base_url}}"
    >>>     ]
    ```

    This component is generic, and does not define resources requirements,
    if for instance this component is hosted on github and you don't
    want to modify the component while at the same time you want to request a GPU for the notebook,
    you can patch the run:

    ```yaml
    >>> version: 1.1
    >>> kind: operation
    >>> urlRef: https://raw.githubusercontent.com/org/repo/master/components/notebook.yaml
    >>> runPatch:
    >>>   container:
    >>>     resources:
    >>>       limits:
    >>>         nvidia.com/gpu: 1
    ```

    By applying a run patch you can effectively share components while having
    full control over customizable details.

    ### hubRef

    Polyaxon provides a [Component Hub](/docs/management/component-hub/)
    for hosting versioned components with an access control system to improve
    the productivity of your team.

    To run a component hosted on Polyaxon Component Hub, you can use `hubRef`

    ```yaml
    >>> version: 1.1
    >>> kind: operation
    >>> hubRef: myComponent:v1.1
    ...
    ```

    ### dagRef

    If you are building a dag and you have a component that can be used by several operations,
    you can define a component and reuse it in all operations using `dagRef`.
    Please check Polyaxon automation's [flow engine section](/docs/automation/flow-engine/)
    for more details.

    ### urlRef

    You can host your components on an accessible url, e.g github,
    and reference those components without downloading the data manually.

    ```yaml
    >>> version: 1.1
    >>> kind: operation
    >>> urlRef: https://raw.githubusercontent.com/org/repo/master/components/my-component.yaml
    ...
    ```

    > Please note that you can only use this reference when using the CLI tool.

    ### pathRef

    In many situations, components can be placed in different folders within a project, e.g.
    data-processing, data-exploration, ml-modeling, ...

    You can define operations without the need to change
    the directory by referencing a path to that component:

    ```yaml
    >>> version: 1.1
    >>> kind: operation
    >>> pathRef: ../data-processing/component-clean.yaml
    ...
    ```

    > Please note that you can only use this reference when using the CLI tool.

    ### component

    If you are still in the development phase or if you are building a
    singleton operation that can be executed in a unique way, you can define
    the component inline inside the operation:

    ```yaml
    >>> version: 1.1
    >>> kind: operation
    >>> component:
    >>>   run:
    >>>      kind: job
    >>>      container:
    >>>        image: foo:latest
    >>>        command: train --lr=0.01
    ...
    ```

    ### isApproved

    This is a flag to trigger human validation before queuing and scheduling an operation.
    the default behavior is `True` even when the field is not set, i.e. no validation is required.
    To require a human validation prior to scheduling an operation,
    you can set this field to `False`.

    ```yaml
    >>> isApproved: false
    ```

    ### Cost

    A field to define the cost of running the operation, the value is a float and should map to a
    convention of a cost estimation in your team or
    it can map directly to the cost of using the environment where the operation is running.

    ```yaml
    >>> cost: 2.2
    ```
    """

    _IDENTIFIER = "operation"
    _FIELDS_MANUAL_PATCH = [
        "version",
        "is_preset",
        "hub_ref",
        "dag_ref",
        "url_ref",
        "path_ref",
        "component",
        "run_patch",
        "patch_strategy",
    ]

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    params: Optional[Dict[StrictStr, V1Param]]
    hub_ref: Optional[StrictStr] = Field(alias="hubRef")
    dag_ref: Optional[StrictStr] = Field(alias="dagRef")
    url_ref: Optional[StrictStr] = Field(alias="urlRef")
    path_ref: Optional[StrictStr] = Field(alias="pathRef")
    component: Optional[V1Component]
    patch_strategy: Optional[PatchStrategy] = Field(alias="patchStrategy")
    is_preset: Optional[bool] = Field(alias="isPreset")
    run_patch: Optional[Dict] = Field(alias="runPatch")
    template: Optional[V1Template]

    @root_validator
    @skip_partial
    def validate_reference(cls, values):
        if not values:
            return values
        if values.get("is_preset"):
            return values
        count = 0
        hub_ref = values.get("hub_ref")
        if hub_ref:
            count += 1
        dag_ref = values.get("dag_ref")
        if dag_ref:
            count += 1
        url_ref = values.get("url_ref")
        if url_ref:
            count += 1
        path_ref = values.get("path_ref")
        if path_ref:
            count += 1
        component = values.get("component")
        if component and count == 0:
            count += 1

        if count != 1:
            raise ValueError(
                "One and only one reference must be specified: "
                "hub_ref, dag_ref, url_ref, path_ref, component."
            )
        return values

    @validator("run_patch")
    @skip_partial
    def validate_run_patch(cls, run_patch, values):
        component = values.get("component")
        if values.get("is_preset"):
            return run_patch
        if not component or not run_patch:
            return run_patch

        validate_run_patch(run_patch=run_patch, kind=component.run.kind)
        return run_patch

    @property
    def has_component_reference(self) -> bool:
        return self.component is not None

    @property
    def has_dag_reference(self) -> bool:
        return bool(self.dag_ref)

    @property
    def has_hub_reference(self) -> bool:
        return bool(self.hub_ref)

    @property
    def has_path_reference(self) -> bool:
        return bool(self.path_ref)

    @property
    def has_url_reference(self) -> bool:
        return bool(self.url_ref)

    @property
    def reference(self):
        if self.has_component_reference:
            return self.component
        if self.has_dag_reference:
            return V1DagRef(name=self.dag_ref)
        if self.has_hub_reference:
            return V1HubRef(name=self.hub_ref)
        if self.has_path_reference:
            return V1PathRef(path=self.path_ref)
        if self.has_url_reference:
            return V1UrlRef(url=self.url_ref)

    @property
    def definition(self):
        if self.has_component_reference:
            return self.component
        if self.has_dag_reference:
            return V1DagRef(name=self.dag_ref)
        if self.has_hub_reference:
            return V1HubRef(name=self.hub_ref)
        if self.has_path_reference:
            return V1PathRef(path=self.path_ref)
        if self.has_url_reference:
            return V1UrlRef(url=self.url_ref)

    def set_definition(self, value):
        self.component = value

    @classmethod
    def patch_obj(cls, config, values, strategy: PatchStrategy = None):
        strategy = strategy or PatchStrategy.POST_MERGE

        result = super().patch_obj(config, values, strategy)
        value = getattr(values, "run_patch", None)
        if value is None:
            return result

        current_value = getattr(config, "run_patch", None)
        if current_value is None:
            setattr(result, "run_patch", value)
            return result

        if (
            not config.component
            or not config.component.run
            or not config.component.run.kind
        ):
            # We don't have a kind, we don't do anything
            if PatchStrategy.is_null(strategy):
                return result
            if PatchStrategy.is_replace(strategy):
                setattr(result, "run_patch", value)
                return result
            return result

        kind = config.component.run.kind
        value = validate_run_patch(value, kind)
        current_value = validate_run_patch(current_value, kind)
        run_patch = current_value.patch(value, strategy)
        run_patch = run_patch.to_dict()
        run_patch.pop("kind")
        result.run_patch = run_patch
        return result

    @classmethod
    def from_hook(cls, hook: V1Hook, contexts: Dict):
        run_patch = None
        if hook.connection:
            run_patch = {"connections": [hook.connection]}
        params = hook.params
        # Extend params with
        if not hook.disable_defaults:
            contexts = contexts or {}
            params = params or {}
            for k, v in contexts.items():
                params[k] = V1Param(value=v, context_only=True)

        return cls.construct(
            run_patch=run_patch,
            hub_ref=hook.hub_ref,
            presets=hook.presets,
            queue=hook.queue,
            namespace=hook.namespace,
            params=params,
        )

    @classmethod
    def from_build(cls, build: V1Build, contexts: Optional[Dict] = None):
        # Extend params with
        contexts = contexts or {}
        params = copy(build.params or {})
        for k, v in contexts.items():
            params[k] = V1Param(value=v, context_only=True)

        destination = params.get("destination") or V1Param(value=None)
        if not destination.value:
            destination.value = "{{ globals.project_name }}:{{ globals.uuid }}"
        if not destination.connection or build.connection:
            destination.connection = build.connection
        params["destination"] = destination

        return cls.construct(
            run_patch=build.run_patch,
            patch_strategy=build.patch_strategy,
            hub_ref=build.hub_ref,
            presets=build.presets,
            queue=build.queue,
            namespace=build.namespace,
            cache=build.cache,
            params=params,
        )


PartialV1Operation = to_partial(V1Operation)
