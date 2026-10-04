from collections.abc import Mapping
from copy import copy, deepcopy
from typing import Dict, List, Optional, Union
from typing_extensions import Literal

from clipped.compact.pydantic import (
    Field,
    StrictStr,
    field_validator,
    model_rebuild,
    model_validator,
    validation_after,
    validation_before,
)
from clipped.config.patch_strategy import PatchStrategy
from clipped.config.schema import skip_partial, to_partial
from clipped.utils.json import orjson_dumps
from polyaxon._flow.base import BaseOp
from polyaxon._flow.builds import V1Build
from polyaxon._flow.hooks import V1Hook
from polyaxon._flow.io import V1IO
from polyaxon._flow.params import V1Param, normalize_param_value
from polyaxon._flow.references import RefMixin, V1DagRef, V1HubRef, V1PathRef, V1UrlRef
from polyaxon._flow.run.dag import V1Dag
from polyaxon._flow.run.patch import patch_run, patch_run_patch, validate_run_patch
from polyaxon._flow.run.runtime import RunMixin, V1Runtime
from polyaxon._flow.templates import TemplateMixinConfig, V1Template
from polyaxon.exceptions import PolyaxonValidationError


class V1Polyaxonfile(BaseOp, TemplateMixinConfig, RunMixin, RefMixin):
    """Shared fields for authored components, operations, and kindless files.

    Root fields may be omitted in reference and preset layers.
    Runtime-dependent validation, including runPatch, belongs after composition.
    """

    _CUSTOM_DUMP_FIELDS = {"run", "component", "termination"}
    _FIELDS_MANUAL_PATCH = [
        "kind",
        "version",
        "is_preset",
        "hub_ref",
        "dag_ref",
        "url_ref",
        "path_ref",
        "component",
        "run",
        "run_patch",
        "patch_strategy",
    ]

    kind: Optional[Literal["component", "operation"]] = None
    inputs: Optional[List[V1IO]] = None
    outputs: Optional[List[V1IO]] = None
    run: Optional[Union[V1Runtime, Dict]] = None
    template: Optional[V1Template] = None
    params: Optional[Dict[StrictStr, V1Param]] = None
    hub_ref: Optional[StrictStr] = Field(alias="hubRef", default=None)
    dag_ref: Optional[StrictStr] = Field(alias="dagRef", default=None)
    url_ref: Optional[StrictStr] = Field(alias="urlRef", default=None)
    path_ref: Optional[StrictStr] = Field(alias="pathRef", default=None)
    component: Optional["V1Polyaxonfile"] = None
    patch_strategy: Optional[PatchStrategy] = Field(alias="patchStrategy", default=None)
    is_preset: Optional[bool] = Field(alias="isPreset", default=None)
    run_patch: Optional[Dict] = Field(alias="runPatch", default=None)

    @model_validator(**validation_before)
    @classmethod
    def parse_component(cls, values):
        if not isinstance(values, Mapping):
            return values
        component = values.get("component")
        if isinstance(component, Mapping):
            model = {
                "component": V1Component,
                "operation": V1Operation,
            }.get(component.get("kind", "component"), V1Polyaxonfile)
            component = model.from_dict(component)
            values = {**values, "component": component}

        return values

    @field_validator("run", **validation_before)
    @classmethod
    def validate_run(cls, run):
        if isinstance(run, Mapping) and "kind" in run:
            # Invalid typed runtimes must not fall back to the Dict alternative.
            try:
                return validate_run_patch(run, run["kind"])
            except PolyaxonValidationError as e:
                raise ValueError(
                    "Unsupported run.kind: {!r}.".format(run["kind"])
                ) from e
        return run

    @field_validator("params", **validation_before)
    @classmethod
    def validate_params(cls, params):
        if not isinstance(params, Mapping):
            return params
        return {k: normalize_param_value(v) for k, v in params.items()}

    @model_validator(**validation_after)
    @skip_partial
    def validate_reference(cls, values):
        if not values or cls.get_value_for_key("is_preset", values):
            return values
        references = ("hub_ref", "dag_ref", "url_ref", "path_ref")
        count = sum(bool(cls.get_value_for_key(ref, values)) for ref in references)
        if count > 1:
            raise ValueError(
                "At most one reference may be specified: "
                "hub_ref, dag_ref, url_ref, path_ref."
            )
        if (
            isinstance(cls.get_value_for_key("run", values), Mapping)
            and not count
            and cls.get_value_for_key("component", values) is None
        ):
            raise ValueError(
                "run.kind must be provided locally or by a referenced base."
            )
        # Stored files can retain both a reference and its resolved component.
        return values

    def to_source_json(self) -> str:
        """Serialize authored fields as JSON, preserving nulls and omissions."""
        return self.to_json(exclude_none=False, exclude_unset=True, purpose="source")

    def to_component_state_dict(self) -> Dict:
        """Project legacy component-state input without changing authored fields."""
        # Reuse validated children; only root kind and its field presence change.
        values = {
            field: getattr(self, field) for field in V1Component.get_model_fields()
        }
        values["kind"] = "component"
        component = V1Component.model_construct(
            _fields_set=self.model_fields_set | {"kind"}, **values
        )
        return component.to_dict(
            humanize_values=False,
            include_kind=False,
            include_version=False,
            exclude_none=True,
            exclude_unset=True,
            exclude_defaults=False,
            purpose="component_state",
        )

    def to_component_state_json(self) -> str:
        """Serialize legacy state input without canonicalizing key order."""
        return orjson_dumps(self.to_component_state_dict())

    def get_run_kind(self):
        return self.run.kind if self.run and not isinstance(self.run, Mapping) else None

    def get_replica_types(self):
        if self.is_distributed_run:
            return self.run.get_replica_types()

    def get_kind_value(self):
        return self.name

    def get_run_dict(self):
        config_dict = self.to_light_dict()
        config_dict.pop("tag", None)
        return config_dict

    def get_name(self):
        return self.name.split(":")[0] if self.name else None

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
        return self.reference

    def set_definition(self, value):
        self.component = value

    def get_native_run(self):
        run = self.component.get_native_run() if self.component is not None else None
        if "run" in self.model_fields_set:
            if isinstance(self.run, Mapping) and run is None:
                return None
            run = patch_run(run, deepcopy(self.run), self.patch_strategy)
        return run

    @classmethod
    def patch_obj(cls, config, values, strategy: PatchStrategy = None):
        strategy = strategy or PatchStrategy.POST_MERGE
        result = super().patch_obj(config, values, strategy)
        if "run" in getattr(values, "model_fields_set", set()):
            base = config.get_native_run()
            if base is None and config.component is not None:
                base = config.component.get_native_run()
            result.run = patch_run(
                config.run,
                deepcopy(values.run),
                strategy,
                base=base,
            )

        value = getattr(values, "run_patch", None)
        if value is not None:
            run = config.get_native_run()
            result.run_patch = patch_run_patch(
                current=config.run_patch,
                value=value,
                kind=run.kind if run is not None else None,
                replica_types=(
                    run.get_replica_types()
                    if run is not None and hasattr(run, "get_replica_types")
                    else None
                ),
                strategy=strategy,
            )
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

        content = {"run_patch": run_patch, "params": params}
        if hook.hub_ref:
            content["hub_ref"] = hook.hub_ref
        if hook.presets:
            content["presets"] = hook.presets
        if hook.queue:
            content["queue"] = hook.queue
        if hook.namespace:
            content["namespace"] = hook.namespace
        return cls.model_construct(**content)

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
        content = {
            "run_patch": build.run_patch,
            "patch_strategy": build.patch_strategy,
            "params": params,
        }
        if build.hub_ref:
            content["hub_ref"] = build.hub_ref
        if build.presets:
            content["presets"] = build.presets
        if build.queue:
            content["queue"] = build.queue
        if build.namespace:
            content["namespace"] = build.namespace
        if build.cache:
            content["cache"] = build.cache

        return cls.model_construct(**content)

    def has_mount(self):
        return bool(self.mount or (self.component and self.component.has_mount()))


class V1Component(V1Polyaxonfile):
    """Component is a discrete, repeatable, and self-contained action that defines
    an environment and a runtime.

    A component is made of code that performs an action,
    such as container building, data preprocessing, data transformation, model training, and so on.

    You can use any language to write the logic of your component,
    Polyaxon uses containers to execute that logic.

    Components are definitions that can be shared if they reach a
    certain maturity and can be managed by the [Component Hub](/docs/registry/component-hub/).
    This allows you to create a library of frequently-used components and reuse them
    either by submitting them directly or by referencing them from your operations.

    Components can be used as well to extract as much information and be used as templates
    with default queues, container resources requirements, node scheduling, ...

    Args:
        version: float, optional
        kind: str, should be equal to `component`
        name: str, optional
        description: str, optional
        tags: List[str], optional
        presets: List[str], optional
        strict_params: bool, optional, effective default is false
        queue: str, optional
        namespace: str, optional
        cache: [V1Cache](/docs/references/polyaxonfile/helpers/cache/), optional
        termination: [V1Termination](/docs/references/polyaxonfile/specification/termination/), optional
        plugins: [V1Plugins](/docs/references/polyaxonfile/specification/plugins/), optional
        mount: List[[V1Mount](/docs/references/polyaxonfile/specification/mount/)], optional
        build: [V1Build](/docs/references/polyaxonfile/orchestration/build/specification/), optional
        hooks: List[[V1Hook](/docs/references/polyaxonfile/orchestration/hooks/specification/)], optional
        inputs: [V1IO](/docs/references/polyaxonfile/specification/io/), optional
        outputs: [V1IO](/docs/references/polyaxonfile/specification/io/), optional
        run: Union[[V1Job](/docs/references/polyaxonfile/runtimes/jobs/specification/), [V1Service](/docs/references/polyaxonfile/runtimes/services/specification/), [V1TFJob](/docs/references/polyaxonfile/runtimes/distributed/tf-jobs/), [V1PytorchJob](/docs/references/polyaxonfile/runtimes/distributed/pytorch-jobs/), [V1MPIJob](/docs/references/polyaxonfile/runtimes/distributed/mpi-jobs/), [V1RayCluster](/docs/references/polyaxonfile/runtimes/clusters/ray-clusters/), [V1DaskCluster](/docs/references/polyaxonfile/runtimes/clusters/dask-clusters/), [V1Dag](/docs/references/polyaxonfile/orchestration/dag/specification/)]  # noqa
        template: [V1Template](/docs/references/polyaxonfile/specification/template/), optional

    ## YAML usage

    ```yaml
    >>> component:
    >>>   version: 1.1
    >>>   kind: component
    >>>   name:
    >>>   description:
    >>>   tags:
    >>>   presets:
    >>>   strictParams:
    >>>   queue:
    >>>   namespace:
    >>>   cache:
    >>>   termination:
    >>>   plugins:
    >>>   actions:
    >>>   hooks:
    >>>   inputs:
    >>>   outputs:
    >>>   mount:
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
    >>>     strict_params=True,
    >>>     queue="test",
    >>>     namespace="test",
    >>>     cache=V1Cache(...),
    >>>     termination=V1Termination(...),
    >>>     plugins=V1Plugins(...),
    >>>     hooks=[V1Hook(...)],
    >>>     inputs=[V1IO(...)],
    >>>     outputs=[V1IO(...)],
    >>>     mount=[V1Mount(...)],
    >>>     build=V1Build(...),
    >>>     run=...
    >>> )
    ```

    ## Fields

    ### version

    The optional Polyaxonfile version. Supplied values are retained for compatibility
    but do not select a validation schema. Older CLI and server versions may require
    `version: 1.1`.

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

    The default component [presets](/docs/scheduling/scheduling-presets/).

    These presets will be passed as the default value to all operations using this component,
    unless the operations override the presets or `--presets`
    is passed as an argument to the cli/client.

    ```yaml
    >>> component:
    >>>   presets: [test]
    ```

    ### strictParams

    > **Note**: Available in Polyaxon 2.18+.

    Set to `true` to require params to match declared inputs/outputs unless they
    explicitly set `contextOnly: true`. Declared IO validation always applies.
    With the default permissive policy, undeclared params become context values.

    ```yaml
    >>> component:
    >>>   strictParams: true
    ```

    Presets and overrides are applied before the component and operation policies
    are combined. Either can enable strict mode; an operation with
    `strictParams: false` cannot relax a strict component. Omitting the field
    preserves existing policy when patching.

    See [params](/docs/references/polyaxonfile/specification/params/) for examples,
    CLI overrides, and version compatibility.

    ### queue

    The default component [queue](/docs/scheduling/scheduling-strategies/queues/).

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

    The default component [cache](/docs/references/polyaxonfile/helpers/cache/).

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

    The default component [termination](/docs/references/polyaxonfile/specification/termination/).

    This termination definition will be passed as the default value to
    all operations using this component,
    unless the operations override the termination.

    ```yaml
    >>> component:
    >>>   termination:
    >>>     maxRetries: 2
    ```

    ### plugins

    The default component [plugins](/docs/references/polyaxonfile/specification/plugins/).

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

    The [inputs](/docs/references/polyaxonfile/specification/io/) definition for this component.

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

    The [outputs](/docs/references/polyaxonfile/specification/io/) definition for this component.

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

    ### mount

    > **Note**: ver 2.13+. Please check [V1Mount](/docs/references/polyaxonfile/specification/mount/) for more details.

    This section defines a list of mounts to be used for this operation.
    Mounts can be defined either as strings or as full objects.
    ```yaml
    >>> operation:
    >>>   ...
    >>>   mount:
    >>>     - /path/in/host:/path/in/container  # defined as string
    >>>     - path_from: /path/in/host          # defined as object
    >>>       path_to: /path/in/container
    >>>   ...
    ```

    ### build

    > **Note**: Please check [V1Build](/docs/references/polyaxonfile/orchestration/build/specification/) for more details.

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
     * [V1Job](/docs/references/polyaxonfile/runtimes/jobs/specification/): for running batch jobs, model training experiments,
       data processing jobs, ...
     * [V1Service](/docs/references/polyaxonfile/runtimes/services/specification/): for running tensorboards, notebooks,
       streamlit, custom services or an API.
     * [V1TFJob](/docs/references/polyaxonfile/runtimes/distributed/tf-jobs/): for running distributed
       Tensorflow training job.
     * [V1PytorchJob](/docs/references/polyaxonfile/runtimes/distributed/pytorch-jobs/): for running distributed
       Pytorch training job.
     * [V1MPIJob](/docs/references/polyaxonfile/runtimes/distributed/mpi-jobs/): for running distributed MPI job.
     * [V1RayCluster](/docs/references/polyaxonfile/runtimes/clusters/ray-clusters/): for running a ray job.
     * [V1DaskCluster](/docs/references/polyaxonfile/runtimes/clusters/dask-clusters/): for running a Dask job.
     * [V1Dag](/docs/references/polyaxonfile/orchestration/dag/specification/): for running a DAG/workflow.

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

    kind: Literal["component"] = _IDENTIFIER


class V1Operation(V1Polyaxonfile):
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

    ![polyaxonfile operation](/images/references/specification/operation.png)

    Args:
        version: float, optional
        kind: str, should be equal to `operation`
        patch_strategy: str, optional, defaults to post_merge
        is_preset: bool, optional
        is_approved: bool, optional
        name: str, optional
        description: str, optional
        tags: List[str], optional
        presets: str, optional
        strict_params: bool, optional, effective default is false
        queue: str, optional
        namespace: str, optional
        cache: [V1Cache](/docs/references/polyaxonfile/helpers/cache/), optional
        termination: [V1Termination](/docs/references/polyaxonfile/specification/termination/), optional
        plugins: [V1Plugins](/docs/references/polyaxonfile/specification/plugins/), optional
        params: Dict[str, [V1Param](/docs/references/polyaxonfile/specification/params/)], optional
        schedule: Union[[V1CronSchedule](/docs/references/polyaxonfile/orchestration/schedules/cron/), [V1IntervalSchedule](/docs/references/polyaxonfile/orchestration/schedules/interval/), [V1DateTimeSchedule](/docs/references/polyaxonfile/orchestration/schedules/datetime/)], optional  # noqa
        events: List[[V1EventTrigger](/docs/references/polyaxonfile/orchestration/events/specification/)], optional
        mount: List[[V1Mount](/docs/references/polyaxonfile/specification/mount/)], optional
        build: [V1Build](/docs/references/polyaxonfile/orchestration/build/specification/), optional
        hooks: List[[V1Hook](/docs/references/polyaxonfile/orchestration/hooks/specification/)], optional
        matrix: Union[[V1Mapping](/docs/references/polyaxonfile/orchestration/mapping/specification/), [V1GridSearch](/docs/references/polyaxonfile/orchestration/matrix/grid-search/), [V1RandomSearch](/docs/references/polyaxonfile/orchestration/matrix/random-search/), [V1Hyperband](/docs/references/polyaxonfile/orchestration/matrix/hyperband/), [V1Bayes](/docs/references/polyaxonfile/orchestration/matrix/bayesian-optimization/), [V1TPE](/docs/references/polyaxonfile/orchestration/matrix/tpe/), [V1Iterative](/docs/references/polyaxonfile/orchestration/matrix/iterative/)], optional  # noqa
        joins: List[[V1Join](/docs/references/polyaxonfile/orchestration/joins/specification/)], optional
        dependencies: [dependencies](/docs/references/polyaxonfile/orchestration/dag/dependencies/#dependencies), optional  # noqa
        trigger: [trigger](/docs/references/polyaxonfile/orchestration/dag/dependencies/#trigger), optional
        conditions: [conditions](/docs/scheduling/scheduling-strategies/conditional-scheduling/#conditional-scheduling), optional  # noqa
        skip_on_upstream_skip: [skip_on_upstream_skip](/docs/references/polyaxonfile/orchestration/dag/dependencies/#skiponupstreamskip), optional  # noqa
        run_patch: Dict, optional
        hub_ref: str, optional
        dag_ref: str, optional
        url_ref: str, optional
        path_ref: str, optional
        component: [V1Component](/docs/references/polyaxonfile/specification/component/), optional
        template: [V1Template](/docs/references/polyaxonfile/specification/template/), optional

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
    >>>   strictParams:
    >>>   queue:
    >>>   namespace:
    >>>   cache:
    >>>   termination:
    >>>   plugins:
    >>>   events:
    >>>   actions:
    >>>   hooks:
    >>>   params:
    >>>   mount:
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
    >>>     strict_params=True,
    >>>     queue="test",
    >>>     namespace="test",
    >>>     cache=V1Cache(...),
    >>>     termination=V1Termination(...),
    >>>     plugins=V1Plugins(...),
    >>>     events=["event-ref1", "event-ref2"],
    >>>     hooks=[V1Hook(...)],
    >>>     outputs={"param1": V1Param(...), ...},
    >>>     mount=[V1Mount(...)],
    >>>     build=V1Build(...),
    >>>     component=V1Component(...),
    >>> )
    ```

    ## Fields

    ### version

    The optional Polyaxonfile version. Supplied values are retained for compatibility
    but do not select a validation schema. Older CLI and server versions may require
    `version: 1.1`.

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
    > [in-depth section about presets](/docs/scheduling/scheduling-presets/).

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

    The [presets](/docs/administration/organizations/presets/) to use for this operation run,
    if provided, it will override the component's presets otherwise
    the presets of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   presets: [test]
    ```

    ### strictParams

    > **Note**: Available in Polyaxon 2.18+.

    Set to `true` to reject undeclared params unless they explicitly set
    `contextOnly: true`. The effective policy is strict if either the component or
    operation is strict after presets and overrides have been applied.

    ```yaml
    >>> operation:
    >>>   strictParams: true
    ```

    Setting this field to `false` cannot relax a strict component. Omitting it
    preserves the operation's policy during patching. If neither object enables
    strict mode, undeclared params become context values by default.

    `polyaxon run` and `polyaxon check` accept `--strict-params` and
    `--no-strict-params` to set this operation field. Additional `-f` preset files
    retain their existing patch order. The compiled operation stores the effective
    policy, which is preserved for scheduled runs and matrix children. Independently
    defined DAG operations use their own policies.

    See [params](/docs/references/polyaxonfile/specification/params/) for examples
    and version compatibility.

    ### queue

    The [queue](/docs/scheduling/scheduling-strategies/queues/) to use for this operation run,
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

    The [cache](/docs/references/polyaxonfile/helpers/cache/) to use for this operation run,
    if provided, it will override the component's cache otherwise
    the cache of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   cache:
    >>>     disable: false
    >>>     ttl: 100
    ```

    ### termination

    The [termination](/docs/references/polyaxonfile/specification/termination/) to use for this operation run,
    if provided, it will override the component's termination otherwise
    the termination of the component will be used if it exists.

    ```yaml
    >>> operation:
    >>>   termination:
    >>>     maxRetries: 2
    ```

    ### plugins

    The [plugins](/docs/references/polyaxonfile/specification/plugins/) to use for this operation run,
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

    The [params](/docs/references/polyaxonfile/specification/params/) to pass to the
    component. Params matching declared inputs/outputs retain their validation.
    In Polyaxon 2.18+, undeclared params become context values by default. With
    `strictParams: true`, they must explicitly set `contextOnly: true`.
    An explicit `contextOnly: false` requires a matching declaration in either mode.

    ```yaml
    >>> operation:
    >>>   params:
    >>>     param1: {value: 1.1}
    >>>     param2: {value: test}
    >>>     param3: {ref: ops.upstream-operation, value: outputs.metric}
    >>>   ...
    ```

    ### mount

    > **Note**: ver 2.13+. Please check [V1Mount](/docs/references/polyaxonfile/specification/mount/) for more details.

    This section defines a list of mounts to be used for this operation.
    Mounts can be defined either as strings or as full objects.
    ```yaml
    >>> operation:
    >>>   ...
    >>>   mount:
    >>>     - /path/in/host:/path/in/container  # defined as string
    >>>     - path_from: /path/in/host          # defined as object
    >>>       path_to: /path/in/container
    >>>   ...
    ```

    ### build

    > **Note**: Please check [V1Build](/docs/references/polyaxonfile/orchestration/build/specification/) for more details.

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

     * [V1Job](/docs/references/polyaxonfile/runtimes/jobs/specification/): for running batch jobs, model training experiments, data processing jobs, ...  # noqa
     * [V1Service](/docs/references/polyaxonfile/runtimes/services/specification/): for running tensorboards, notebooks, streamlit, custom services or an API.  # noqa
     * [V1TFJob](/docs/references/polyaxonfile/runtimes/distributed/tf-jobs/): for running distributed Tensorflow training job.  # noqa
     * [V1PytorchJob](/docs/references/polyaxonfile/runtimes/distributed/pytorch-jobs/): for running distributed Pytorch training job.  # noqa
     * [V1MPIJob](/docs/references/polyaxonfile/runtimes/distributed/mpi-jobs/): for running distributed MPI job.  # noqa
     * [V1RayCluster](/docs/references/polyaxonfile/runtimes/clusters/ray-clusters/): for running a Ray cluster.
     * [V1DaskCluster](/docs/references/polyaxonfile/runtimes/clusters/dask-clusters/): for running a Dask cluster.
     * [V1Dag](/docs/references/polyaxonfile/orchestration/dag/specification/): for running a DAG/workflow.

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

    Polyaxon provides a [Component Hub](/docs/registry/component-hub/)
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
    Please check Polyaxon orchestration's [flow engine section](/docs/references/polyaxonfile/orchestration/dag/overview/)
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

    kind: Literal["operation"] = _IDENTIFIER


PartialV1Polyaxonfile = to_partial(V1Polyaxonfile)
PartialV1Operation = to_partial(V1Operation)

# Resolve the single DAG runtime after all recursive authoring models exist.
for model in (
    V1Dag,
    V1Polyaxonfile,
    V1Component,
    V1Operation,
    PartialV1Polyaxonfile,
    PartialV1Operation,
):
    model_rebuild(
        model,
        V1Polyaxonfile=V1Polyaxonfile,
        V1Component=V1Component,
        V1Operation=V1Operation,
    )
