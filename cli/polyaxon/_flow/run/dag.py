from collections.abc import Mapping
from typing import Any, Dict, ForwardRef, List, Optional, Set, Union
from typing_extensions import Literal

from clipped.compact.pydantic import (
    Field,
    PositiveInt,
    PrivateAttr,
    StrictStr,
    field_validator,
    validation_always,
    validation_before,
)
from clipped.types.ref_or_obj import RefField
from polyaxon import types
from polyaxon._contexts import sections as ctx_sections
import polyaxon._flow.dags as dags
from polyaxon._flow.early_stopping import V1EarlyStopping
from polyaxon._flow.environment import V1Environment
from polyaxon._flow.io import V1IO
from polyaxon._flow.params import ops_params
from polyaxon._flow.run.base import BaseRun
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon.exceptions import PolyaxonSchemaError


V1Polyaxonfile = ForwardRef("V1Polyaxonfile")


class V1Dag(BaseRun):
    """Dag (Directed Acyclic Graphs) is
    a collection of all the operations you want to run,
    organized in a way that reflects their relationships and dependencies.

    A dag's main goal is to describe and run several operations
    necessary for a Machine Learning (ML) workflow.

    A dag executes a dependency graph of operations, each operation runs a Kubernetes primitive
    described in its component.

    Dags are defined in Polyaxon as a [component runtime](/docs/references/polyaxonfile/specification/component/#run),
    which makes them compatible with all knowledge used for running other runtimes:
     * They can be defined in reusable components and can be registered in the Component Hub.
     * They get executed using operations.
     * They can be parametrized similar to jobs and services.
     * Since they are defined as components' runtimes, and they run a graph of other components,
       they can be nested natively.
     * They can leverage all [pipeline helpers](/docs/references/polyaxonfile/helpers/overview/).
     * They can run in parallel and can be used with [mapping](/docs/references/polyaxonfile/orchestration/mapping/overview/) or
       other [optimization algorithms](/docs/references/polyaxonfile/orchestration/matrix/overview/).
     * They can run on [schedule](/docs/references/polyaxonfile/orchestration/schedules/overview/)
     * They can subscribe to [events](/docs/references/polyaxonfile/orchestration/events/overview/)
     * They can take advantage of all scheduling strategies to route operations to nodes,
       namespaces, and clusters even within the same DAG.

    Args:
        kind: str, should be equal `dag`
        operations: List[[V1Operation](/docs/references/polyaxonfile/specification/operation/)]
        components: List[[V1Component](/docs/references/polyaxonfile/specification/component/)], optional
        environment: [V1Environment](/docs/references/polyaxonfile/specification/environment/), optional
        connections: List[str], optional
        volumes: List[[Kubernetes Volume](https://kubernetes.io/docs/concepts/storage/volumes/)],
             optional
        concurrency: init, optional
        early_stopping: List[[EarlyStopping](/docs/references/polyaxonfile/helpers/early-stopping)], optional

    ## YAML usage

    ```yaml
    >>> run:
    >>>   kind: dag
    >>>   operations:
    >>>   components:
    >>>   environment:
    >>>   connections:
    >>>   volumes:
    >>>   concurrency:
    >>>   earlyStopping:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Dag, V1Component, V1Environment, V1Operation
    >>> from polyaxon import k8s
    >>> dag = V1Dag(
    >>>     operations=[V1Operation(...)],
    >>>     components=[V1Component(...), V1Component(...)],
    >>>     environment=V1Environment(...),
    >>>     connections=["connection-name1"],
    >>>     volumes=[k8s.V1Volume(...)],
    >>> )
    ```

    ## Fields

    ### kind

    The kind signals to the CLI, client, and other tools that this component's runtime is a dag.

    If you are using the python client to create the runtime,
    this field is not required and is set by default.

    ```yaml
    >>> run:
    >>>   kind: dag
    ```

    ### operations

    A list of operations to run with their dependency definition.
    If the operations are defined with no dependencies or no params are
    passed from one operation to another, the operations will be running in parallel following the
    concurrency and other queue priority definitions.

    ```yaml
    >>> run:
    >>>   kind: dag
    >>>   operations:
    >>>     - name: job1
    >>>       hubRef: component1:latest
    >>>       params:
    >>>         ...
    >>>     - name: job2
    >>>       hubRef: component1:2.1
    >>>       params:
    >>>         ...
    >>>     - name: job3
    >>>       urlRef: https://some_url.com
    >>>       params:
    >>>         param1:
    >>>           ref: ops.job2
    >>>           value: outputs.outputName
    >>>
    ```

    > **Note**: For more information about managing the execution graph
    > and creating dependencies between operations, please check the
    > [flow dependencies section](/docs/references/polyaxonfile/orchestration/dag/dependencies/).

    ### references

    A list of operations and their dependency definition.
    If operations are defined with dependencies or no params are
    passed from one operation to another, the operations will be running in parallel following the
    concurrency and other queue priority definitions.

    Operations can reference components using:
        * [dagRef](/docs/references/polyaxonfile/specification/operation/#dagRef)
             (reusable component defined inside the dag)
        * [hubRef](/docs/references/polyaxonfile/specification/operation/#hubRef)
        * [pathRef](/docs/references/polyaxonfile/specification/operation/#pathRef)
        * [urlRef](/docs/references/polyaxonfile/specification/operation/#urlRef)
        * [inline component](/docs/references/polyaxonfile/specification/operation/#component)

    ```yaml
    >>> run:
    >>>   kind: dag
    >>>   operations:
    >>>     - name: download1
    >>>     dagRef: download
    >>>     params:
    >>>       url: {value: 'gs://ml-pipeline-playground/shakespeare1.txt'}
    >>>       result: {value: 'result.txt'}
    >>>     - name: download2
    >>>       dagRef: download
    >>>       params:
    >>>         url: {value: 'gs://ml-pipeline-playground/shakespeare2.txt'}
    >>>         result: {value: 'result.txt'}
    ```

    ### components

    A list of reusable components defined inside the DAG that can be used by one
    or several operations. This field is only useful when you need to define inline components
    for your operations and more than one operation is using the same component definition.

    ```yaml
    >>> operations:
    >>>   - name: download-url1
    >>>     dagRef: download
    >>>     ...
    >>>   - name: download-url2
    >>>     dagRef: download
    >>>     ...
    >>> components:
    >>>   - name: download
    >>>     inputs:
    >>>       - name: url
    >>>         type: url
    >>>     outputs:
    >>>       - name: result
    >>>         type: path
    >>>         delayValidation: false
    >>>     run:
    >>>       kind: job
    >>>       container:
    >>>         image: 'google/cloud-sdk:272.0.0'
    >>>         command: ['sh', '-c'],
    >>>         args: ['gsutil cat $0 | tee $1', "{{ url }}", "{{ outputs_path }}/{{ result }}"]
    ```

    ### environment

    Optional [environment section](/docs/references/polyaxonfile/specification/environment/),
    it provides a way to inject pod related information.

    The environment definition will be passed to all children operations.

    ```yaml
    >>> run:
    >>>   kind: dag
    >>>   environment:
    >>>     labels:
    >>>        key1: "label1"
    >>>        key2: "label2"
    >>>      annotations:
    >>>        key1: "value1"
    >>>        key2: "value2"
    >>>      nodeSelector:
    >>>        node_label: node_value
    >>>      ...
    >>>  ...
    ```

    ### connections

    A list of [connection names](/docs/setup/connections/) to resolve for the dag.

    <blockquote className="light">
    If you are referencing a connection it must be configured.
    All referenced connections will be checked:

     * If they are accessible in the context of the project of this run

     * If the user running the operation can have access to those connections
    </blockquote>

    The connections definition will be passed to all operations.
    After checks, the connections will be resolved and inject any volumes, secrets, configMaps,
    environment variables for your main container to function correctly.

    ```yaml
    >>> run:
    >>>   kind: dag
    >>>   connections: [connection1, connection2]
    ```

    ### volumes

    A list of [Kubernetes Volumes](https://kubernetes.io/docs/concepts/storage/volumes/)
    to resolve and mount for your jobs.

    This is an advanced use-case where configuring a connection is not an option.

    the volumes definition will be passed to all operations.

    When you add a volume you need to mount it manually to your container(s).

    ```yaml
    >>> run:
    >>>   kind: dag
    >>>   volumes:
    >>>     - name: volume1
    >>>       persistentVolumeClaim:
    >>>         claimName: pvc1
    >>>   ...
    ```
    ### concurrency

    An optional value to set the number of concurrent operations.

    ```yaml
    >>> matrix:
    >>>   kind: dag
    >>>   concurrency: 2
    ```

    For more details about concurrency management,
    please check the [concurrency section](/docs/references/polyaxonfile/helpers/concurrency/).

    ### earlyStopping

    A list of early stopping conditions to check for terminating
    all operations managed by the pipeline.
    If one of the early stopping conditions is met,
    a signal will be sent to terminate all running and pending operations.

    ```yaml
    >>> matrix:
    >>>   kind: dag
    >>>   earlyStopping: ...
    ```

    For more details please check the
    [early stopping section](/docs/references/polyaxonfile/helpers/early-stopping/).

    """

    _IDENTIFIER = V1RunKind.DAG
    _SWAGGER_FIELDS = ["volumes"]
    _CUSTOM_DUMP_FIELDS = {"operations", "components", "environment"}

    kind: Literal[V1RunKind.DAG] = _IDENTIFIER
    operations: Optional[Union[List[V1Polyaxonfile], RefField]] = None
    components: Optional[Union[List[V1Polyaxonfile], RefField]] = None
    environment: Optional[Union[V1Environment, RefField]] = None
    connections: Optional[Union[List[StrictStr], RefField]] = None
    volumes: Optional[Union[List[k8s_schemas.V1Volume], RefField]] = None
    concurrency: Optional[Union[PositiveInt, RefField]] = None
    early_stopping: Optional[Union[List[V1EarlyStopping], RefField]] = Field(
        alias="earlyStopping", default=None
    )

    _dag: Dict[str, "DagOpSpec"] = PrivateAttr()
    _components_by_names: Dict[str, V1Polyaxonfile] = PrivateAttr()
    _op_component_mapping: Dict[str, str] = PrivateAttr()
    _effective_ops: Dict[str, V1Polyaxonfile] = PrivateAttr()
    _context: Dict[str, Any] = PrivateAttr()

    @field_validator("operations", "components", **validation_before)
    def validate_polyaxonfiles(cls, value):
        from polyaxon._flow.polyaxonfile import V1Component, V1Operation, V1Polyaxonfile

        if not isinstance(value, list):
            return value
        models = {"component": V1Component, "operation": V1Operation}
        return [
            models.get(item.get("kind"), V1Polyaxonfile).from_dict(item)
            if isinstance(item, Mapping)
            else item
            for item in value
        ]

    @field_validator("volumes", **validation_always, **validation_before)
    def validate_volumes(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_volume(vi) for vi in v]

    def __init__(self, **data):
        super().__init__(**data)
        self._dag = {}  # OpName -> DagOpSpec
        self._components_by_names = {}  # ComponentName -> Component
        self._op_component_mapping = {}  # OpName -> ComponentName
        self._effective_ops = {}
        self._context = {}  # Ops output names -> types

    @property
    def dag(self):
        return self._dag

    def validate_dag(self, dag=None):
        dag = dag or self.dag
        orphan_ops = self.get_orphan_ops(dag=dag)
        if orphan_ops:
            raise PolyaxonSchemaError(
                "Pipeline has a non valid dag, the dag contains an orphan ops: `{}`, "
                "check if you are referencing this op "
                "in a parameter or a condition".format(orphan_ops)
            )
        self.sort_topologically(dag=dag)

    def _get_op_upstream_from_params(self, op) -> set:
        upstream = set([])
        if not isinstance(op.params, Mapping):
            raise PolyaxonSchemaError(
                "Op `{}` defines a malformed params `{}`, "
                "params should be a dictionary of form <name: Param>".format(
                    op.name, op.params
                )
            )

        for param in op.params.values():
            if param.is_ops_ref:
                upstream.add(param.entity_ref)

        return upstream

    def _get_op_upstream_from_events(self, op) -> set:
        upstream = set([])
        if not isinstance(op.events, list):
            raise PolyaxonSchemaError(
                "Op `{}` defines a malformed events `{}`, "
                "events should be a list of dictionaries of form <List[EventTrigger]>".format(
                    op.name, op.events
                )
            )

        for event in op.events:
            if event.is_ops_ref:
                upstream.add(event.entity_ref)

        return upstream

    def _get_op_upstream(self, op) -> Set:
        upstream = set(op.dependencies) if op.dependencies else set([])

        if op.params:
            upstream |= self._get_op_upstream_from_params(op)

        if op.events:
            upstream |= self._get_op_upstream_from_events(op)

        return upstream

    def _process_op(self, op):
        upstream = self._get_op_upstream(op=self._effective_ops.get(op.name, op))
        self._dag = dags.set_dag_op(
            dag=self.dag, op_id=op.name, op=op, upstream=upstream, downstream=None
        )
        for op_name in upstream:
            self._dag = dags.set_dag_op(
                dag=self.dag, op_id=op_name, downstream=[op.name]
            )

    def process_dag(self):
        for op in self.operations or []:
            self._process_op(op)

    def add_op(self, op):
        self.operations = self.operations or []
        self.operations.append(op)
        self._process_op(op)

    def add_ops(self, ops):
        for op in ops:
            self.add_op(op)

    def get_independent_ops(self, dag=None):
        """Get a list of all node in the graph with no dependencies."""
        return dags.get_independent_ops(self.dag or dag)

    def get_orphan_ops(self, dag=None):
        """Get orphan ops for given dag."""
        return dags.get_orphan_ops(dag or self.dag)

    def sort_topologically(self, dag=None, flatten=False):
        """Sort the dag breath first topologically.

        Only the nodes inside the dag are returned, i.e. the nodes that are also keys.

        Returns:
             a topological ordering of the DAG.
        Raises:
             an error if this is not possible (graph is not valid).
        """

        return dags.sort_topologically(dag or self.dag, flatten=flatten)

    def resolve_operations(self, ignore_hub_validation: bool = False):
        from polyaxon._polyaxonfile.manager.operations import compose_polyaxonfile

        self._components_by_names = {}
        self._op_component_mapping = {}
        self._effective_ops = {}

        if not self.operations:
            raise PolyaxonSchemaError(
                "Pipeline is not valid, it has no ops to validate components."
            )

        components = self.components or []

        for component in components:
            component_name = component.name
            if not component_name:
                raise PolyaxonSchemaError("Pipeline component requires a name.")
            if component_name in self._components_by_names:
                raise PolyaxonSchemaError(
                    "Pipeline has multiple components with the same name `{}`".format(
                        component_name
                    )
                )
            self._components_by_names[component_name] = component

        op_names = set()
        effective_ops = {}
        for op in self.operations:
            op_name = op.name
            if not op_name:
                raise PolyaxonSchemaError("Pipeline op requires a name.")
            if op_name in op_names:
                raise PolyaxonSchemaError(
                    "Pipeline has multiple ops with the same name `{}`".format(op_name)
                )
            op_names.add(op_name)
            if not op.has_component_reference and (
                op.has_hub_reference or op.has_path_reference or op.has_url_reference
            ):
                if op.has_hub_reference and ignore_hub_validation:
                    continue
                raise PolyaxonSchemaError(
                    "Pipeline op has no definition field `{}`".format(op_name)
                )
            if op.has_dag_reference and not op.has_component_reference:
                self._op_component_mapping[op_name] = op.dag_ref
            effective = compose_polyaxonfile(self._get_op_spec(op), is_dag_node=True)
            if effective.run is None:
                raise PolyaxonSchemaError(
                    "Pipeline op has no definition field `{}`".format(op_name)
                )
            effective_ops[op_name] = effective
        self._effective_ops = effective_ops

    def process_components(self, inputs=None, ignore_hub_validation: bool = False):
        """`ignore_hub_validation` is currently used for ignoring validation
        during tests with hub_ref.
        """
        if not self._effective_ops or len(self._effective_ops) != len(
            self.operations or []
        ):
            self.resolve_operations(ignore_hub_validation=ignore_hub_validation)

        inputs = inputs or []
        self._context = {}

        for g_context in ctx_sections.GLOBALS_CONTEXTS:
            self._context[
                "dag.{}.{}".format(ctx_sections.GLOBALS, g_context)
            ] = V1IO.model_construct(name=g_context, type="str", value="", is_optional=True)  # fmt: skip

        self._context["dag.{}".format(ctx_sections.INPUTS)] = V1IO.model_construct(
            name="inputs", type="dict", value={}, is_optional=True
        )
        self._context["dag.{}".format(ctx_sections.GLOBALS)] = V1IO.model_construct(
            name="globals", type="str", value="", is_optional=True
        )
        self._context["dag.{}".format(ctx_sections.ARTIFACTS)] = V1IO.model_construct(
            name="artifacts", type="str", value="", is_optional=True
        )

        for _input in inputs:
            self._context["dag.inputs.{}".format(_input.name)] = _input

        for op in self._effective_ops.values():
            op_name = op.name
            outputs = op.outputs
            inputs = op.inputs

            if outputs:
                for output in outputs:
                    self._context[
                        "ops.{}.{}.{}".format(
                            op_name, ctx_sections.OUTPUTS, output.name
                        )
                    ] = output
                    if output.type == types.ARTIFACTS:
                        self._context[
                            "ops.{}.{}.{}".format(
                                op_name, ctx_sections.ARTIFACTS, output.name
                            )
                        ] = output

            if inputs:
                for cinput in inputs:
                    self._context[
                        "ops.{}.{}.{}".format(op_name, ctx_sections.INPUTS, cinput.name)
                    ] = cinput
                    if cinput.type == types.ARTIFACTS:
                        self._context[
                            "ops.{}.{}.{}".format(
                                op_name, ctx_sections.ARTIFACTS, cinput.name
                            )
                        ] = cinput
            for g_context in ctx_sections.GLOBALS_CONTEXTS:
                self._context[
                    "ops.{}.{}.{}".format(op_name, ctx_sections.GLOBALS, g_context)
                ] = V1IO.model_construct(
                    name=g_context, type="str", value="", is_optional=True
                )

            # We allow to resolve name, status, project, all outputs/inputs, iteration
            self._context[
                "ops.{}.{}".format(op_name, ctx_sections.INPUTS)
            ] = V1IO.model_construct(name="inputs", type="dict", value={}, is_optional=True)  # fmt: skip
            self._context[
                "ops.{}.{}".format(op_name, ctx_sections.OUTPUTS)
            ] = V1IO.model_construct(name="outputs", type="dict", value={}, is_optional=True)  # fmt: skip
            self._context[
                "ops.{}.{}".format(op_name, ctx_sections.GLOBALS)
            ] = V1IO.model_construct(name="globals", type="str", value="", is_optional=True)  # fmt: skip
            self._context[
                "ops.{}.{}".format(op_name, ctx_sections.ARTIFACTS)
            ] = V1IO.model_construct(name="artifacts", type="str", value="", is_optional=True)  # fmt: skip
            self._context[
                "ops.{}.{}".format(op_name, ctx_sections.INPUTS_OUTPUTS)
            ] = V1IO.model_construct(name="io", type="str", value={}, is_optional=True)  # fmt: skip

        for op in self._effective_ops.values():
            ops_params.validate_params(
                params=op.params,
                inputs=op.inputs,
                outputs=op.outputs,
                context=self._context,
                matrix=op.matrix,
                joins=op.joins,
                is_template=False,
                check_all_refs=False,
                extra_info="<op {}>".format(op.name),
                strict_params=op.strict_params,
            )

    def _get_op_spec(self, op):
        from polyaxon._polyaxonfile.specs import read_polyaxonfile

        def resolve_template(config, sources=()):
            if config.component is not None:
                resolve_template(config.component, sources)
            elif config.dag_ref:
                name = config.dag_ref
                if name in sources:
                    raise PolyaxonSchemaError(
                        "Pipeline op `{}` has a template reference cycle: {}".format(
                            op.name, " -> ".join((*sources, name))
                        )
                    )
                if name not in self._components_by_names:
                    raise PolyaxonSchemaError(
                        "Pipeline op with name `{}` requires a component with name `{}`, "
                        "which is not defined on this pipeline.".format(op.name, name)
                    )
                config.component = read_polyaxonfile(self._components_by_names[name])
                resolve_template(config.component, (*sources, name))

        config = read_polyaxonfile(op)
        resolve_template(config)
        return config

    def get_effective_op(self, name):
        return self._effective_ops[name]

    def set_op_component(self, op_name):
        if op_name not in self.dag:
            raise PolyaxonSchemaError(
                "Job with name `{}` was not found in Dag, "
                "make sure to run `process_dag`.".format(op_name)
            )
        op_spec = self.dag[op_name]
        if op_spec.op.has_component_reference or (
            op_spec.op.run is not None and op_spec.op.reference is None
        ):
            return

        if op_name not in self._op_component_mapping:
            raise PolyaxonSchemaError(
                "Pipeline op with name `{}` requires a reference `{} ({})`, "
                "which is not defined on this pipeline, "
                "make sure to run `process_components`".format(
                    op_name,
                    op_spec.op.definition.kind,
                    op_spec.op.definition.get_kind_value(),
                )
            )
        op_spec.op.set_definition(self._get_op_spec(op_spec.op).component)

    def get_op_spec_by_index(self, idx):
        return self._get_op_spec(self.operations[idx])

    def get_op_spec_by_name(self, name):
        return self._get_op_spec(self.dag[name].op)

    def get_resources(self):
        return None

    def get_all_containers(self):
        return []

    def get_all_connections(self):
        return self.connections or []

    def get_all_init(self):
        return []
