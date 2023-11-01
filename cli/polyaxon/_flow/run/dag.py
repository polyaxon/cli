from collections.abc import Mapping
from typing import Any, Dict, ForwardRef, List, Optional, Set, Union
from typing_extensions import Literal

from clipped.compact.pydantic import (
    Field,
    PositiveInt,
    PrivateAttr,
    StrictStr,
    validator,
)
from clipped.types.ref_or_obj import RefField

from polyaxon import types
from polyaxon._contexts import sections as ctx_sections
from polyaxon._flow import dags
from polyaxon._flow.early_stopping import V1EarlyStopping
from polyaxon._flow.environment import V1Environment
from polyaxon._flow.io import V1IO
from polyaxon._flow.params import ops_params
from polyaxon._flow.run.base import BaseRun
from polyaxon._flow.run.enums import V1RunKind
from polyaxon._k8s import k8s_schemas, k8s_validation
from polyaxon.exceptions import PolyaxonSchemaError
from polyaxon.pkg import SCHEMA_VERSION

V1Operation = ForwardRef("V1Operation")
V1Component = ForwardRef("V1Component")


class V1Dag(BaseRun):
    """Dag (Directed Acyclic Graphs) is
    a collection of all the operations you want to run,
    organized in a way that reflects their relationships and dependencies.

    A dag's main goal is to describe and run several operations
    necessary for a Machine Learning (ML) workflow.

    A dag executes a dependency graph of operations, each operation runs a Kubernetes primitive
    described in its component.

    Dags are defined in Polyaxon as a [component runtime](/docs/core/specification/component/#run),
    which makes them compatible with all knowledge used for running other runtimes:
     * They can be defined in reusable components and can be registered in the Component Hub.
     * They get executed using operations.
     * They can be parametrized similar to jobs and services.
     * Since they are defined as components' runtimes, and they run a graph of other components,
       they can be nested natively.
     * They can leverage all [pipeline helpers](/docs/automation/helpers/).
     * They can run in parallel and can be used with [mapping](/docs/automation/mapping/) or
       other [optimization algorithms](/docs/automation/optimization-engine/).
     * They can run on [schedule](/docs/automation/schedules/)
     * They can subscribe to [events](/docs/automation/events/)
     * They can take advantage of all scheduling strategies to route operations to nodes,
       namespaces, and clusters even within the same DAG.

    Args:
        kind: str, should be equal `dag`
        operations: List[[V1Operation](/docs/core/specification/operation/)]
        components: List[[V1Component](/docs/core/specification/component/)], optional
        environment: [V1Environment](/docs/core/specification/environment/), optional
        connections: List[str], optional
        volumes: List[[Kubernetes Volume](https://kubernetes.io/docs/concepts/storage/volumes/)],
             optional
        concurrency: init, optional
        early_stopping: List[[EarlyStopping](/docs/automation/helpers/early-stopping)], optional

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
    > [flow dependencies section](/docs/automation/flow-engine/flow-dependencies/).

    ### references

    A list of operations and their dependency definition.
    If operations are defined with dependencies or no params are
    passed from one operation to another, the operations will be running in parallel following the
    concurrency and other queue priority definitions.

    Operations can reference components using:
        * [dagRef](/docs/core/specification/operation/#dagRef)
             (reusable component defined inside the dag)
        * [hubRef](/docs/core/specification/operation/#hubRef)
        * [pathRef](/docs/core/specification/operation/#pathRef)
        * [urlRef](/docs/core/specification/operation/#urlRef)
        * [inline component](/docs/core/specification/operation/#component)

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

    Optional [environment section](/docs/core/specification/environment/),
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

    <blockquote class="light">
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
    please check the [concurrency section](/docs/automation/helpers/concurrency/).

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
    [early stopping section](/docs/automation/helpers/early-stopping/).

    """

    _IDENTIFIER = V1RunKind.DAG
    _SWAGGER_FIELDS = ["volumes"]

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    operations: Optional[Union[List[V1Operation], RefField]]
    components: Optional[Union[List[V1Component], RefField]]
    environment: Optional[Union[V1Environment, RefField]]
    connections: Optional[Union[List[StrictStr], RefField]]
    volumes: Optional[Union[List[k8s_schemas.V1Volume], RefField]]
    concurrency: Optional[Union[PositiveInt, RefField]]
    early_stopping: Optional[Union[List[V1EarlyStopping], RefField]] = Field(
        alias="earlyStopping"
    )

    _dag: Dict[str, "DagOpSpec"] = PrivateAttr()
    _components_by_names: Dict[str, V1Component] = PrivateAttr()
    _op_component_mapping: Dict[str, str] = PrivateAttr()
    _context: Dict[str, Any] = PrivateAttr()

    @validator("volumes", always=True, pre=True)
    def validate_volumes(cls, v):
        if not v:
            return v
        return [k8s_validation.validate_k8s_volume(vi) for vi in v]

    def __init__(self, **data):
        super().__init__(**data)
        self._dag = {}  # OpName -> DagOpSpec
        self._components_by_names = {}  # ComponentName -> Component
        self._op_component_mapping = {}  # OpName -> ComponentName
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
        upstream = self._get_op_upstream(op=op)
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

    def process_components(self, inputs=None, ignore_hub_validation: bool = False):
        """`ignore_hub_validation` is currently used for ignoring validation
        during tests with hub_ref.
        """
        inputs = inputs or []

        for g_context in ctx_sections.GLOBALS_CONTEXTS:
            self._context[
                "dag.{}.{}".format(ctx_sections.GLOBALS, g_context)
            ] = V1IO.construct(name=g_context, type="str", value="", is_optional=True)

        self._context["dag.{}".format(ctx_sections.INPUTS)] = V1IO.construct(
            name="inputs", type="dict", value={}, is_optional=True
        )
        self._context["dag.{}".format(ctx_sections.GLOBALS)] = V1IO.construct(
            name="globals", type="str", value="", is_optional=True
        )
        self._context["dag.{}".format(ctx_sections.ARTIFACTS)] = V1IO.construct(
            name="artifacts", type="str", value="", is_optional=True
        )

        for _input in inputs:
            self._context["dag.inputs.{}".format(_input.name)] = _input

        if not self.operations:
            raise PolyaxonSchemaError(
                "Pipeline is not valid, it has no ops to validate components."
            )

        components = self.components or []

        for component in components:
            component_name = component.name
            if component_name in self._components_by_names:
                raise PolyaxonSchemaError(
                    "Pipeline has multiple components with the same name `{}`".format(
                        component_name
                    )
                )
            self._components_by_names[component_name] = component

        for op in self.operations:
            op_name = op.name
            if op.has_component_reference:
                outputs = op.component.outputs
                inputs = op.component.inputs
            elif op.has_dag_reference:
                component_ref_name = op.dag_ref
                if op_name in self._op_component_mapping:
                    raise PolyaxonSchemaError(
                        "Pipeline has multiple ops with the same name `{}`".format(
                            op_name
                        )
                    )
                if component_ref_name not in self._components_by_names:
                    raise PolyaxonSchemaError(
                        "Pipeline op with name `{}` requires a component with name `{}`, "
                        "which is not defined on this pipeline.".format(
                            op_name, component_ref_name
                        )
                    )
                self._op_component_mapping[op_name] = component_ref_name
                outputs = self._components_by_names[component_ref_name].outputs
                inputs = self._components_by_names[component_ref_name].inputs
            elif op.has_hub_reference and ignore_hub_validation:
                continue
            else:
                raise PolyaxonSchemaError(
                    "Pipeline op has no definition field `{}`".format(op_name)
                )

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
                ] = V1IO.construct(
                    name=g_context, type="str", value="", is_optional=True
                )

            # We allow to resolve name, status, project, all outputs/inputs, iteration
            self._context[
                "ops.{}.{}".format(op_name, ctx_sections.INPUTS)
            ] = V1IO.construct(name="inputs", type="dict", value={}, is_optional=True)
            self._context[
                "ops.{}.{}".format(op_name, ctx_sections.OUTPUTS)
            ] = V1IO.construct(name="outputs", type="dict", value={}, is_optional=True)
            self._context[
                "ops.{}.{}".format(op_name, ctx_sections.GLOBALS)
            ] = V1IO.construct(name="globals", type="str", value="", is_optional=True)
            self._context[
                "ops.{}.{}".format(op_name, ctx_sections.ARTIFACTS)
            ] = V1IO.construct(name="artifacts", type="str", value="", is_optional=True)
            self._context[
                "ops.{}.{}".format(op_name, ctx_sections.INPUTS_OUTPUTS)
            ] = V1IO.construct(name="io", type="str", value={}, is_optional=True)

        for op in self.operations:
            if op.has_component_reference:
                component_ref = op.definition.name
                outputs = op.definition.outputs
                inputs = op.definition.inputs
            elif op.has_dag_reference:
                component_ref = op.definition.name
                outputs = self._components_by_names[component_ref].outputs
                inputs = self._components_by_names[component_ref].inputs
            elif op.has_hub_reference and ignore_hub_validation:
                continue
            else:
                raise PolyaxonSchemaError(
                    "Pipeline op has no definition field `{}`".format(op.name)
                )
            ops_params.validate_params(
                params=op.params,
                inputs=inputs,
                outputs=outputs,
                context=self._context,
                matrix=op.matrix,
                joins=op.joins,
                is_template=False,
                check_all_refs=False,
                extra_info="<op {}>.<component {}>".format(op.name, component_ref),
            )

    def set_op_component(self, op_name):
        if op_name not in self.dag:
            raise PolyaxonSchemaError(
                "Job with name `{}` was not found in Dag, "
                "make sure to run `process_dag`.".format(op_name)
            )
        op_spec = self.dag[op_name]
        if op_spec.op.has_component_reference:
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
        component_ref_name = self._op_component_mapping[op_name]
        op_spec.op.set_definition(self._components_by_names[component_ref_name])

    def get_op_spec_by_index(self, idx):
        from polyaxon._polyaxonfile import OperationSpecification

        op_dict = self.operations[idx].to_dict()
        op_dict[OperationSpecification.VERSION] = op_dict.get(
            OperationSpecification.VERSION, SCHEMA_VERSION
        )
        return OperationSpecification.read(op_dict)

    def get_op_spec_by_name(self, name):
        from polyaxon._polyaxonfile import OperationSpecification

        op_dict = self.dag[name].op.to_dict()
        op_dict[OperationSpecification.VERSION] = op_dict.get(
            OperationSpecification.VERSION, SCHEMA_VERSION
        )
        return OperationSpecification.read(op_dict)

    def get_resources(self):
        return None

    def get_all_containers(self):
        return []

    def get_all_connections(self):
        return self.connections or []

    def get_all_init(self):
        return []
