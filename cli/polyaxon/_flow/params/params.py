from collections import namedtuple
from collections.abc import Mapping
from typing import Any, Dict, Optional

from clipped.compact.pydantic import Field, StrictStr, field_validator
from clipped.config.schema import skip_partial
from clipped.utils.lists import to_list
from clipped.utils.strings import to_string

from polyaxon import types
from polyaxon._contexts import refs as ctx_refs
from polyaxon._contexts import sections as ctx_sections
from polyaxon._contexts.params import PARAM_REGEX
from polyaxon._flow.init import V1Init
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon.exceptions import PolyaxonValidationError


# V1Param fields that indicate full-form param definition
# If a dict contains any of these keys, it's a full-form V1Param, not a short-form value
V1_PARAM_KEYS = {
    "value",
    "ref",
    "toInit",
    "to_init",
    "toEnv",
    "to_env",
    "contextOnly",
    "context_only",
    "connection",
}


def is_short_form_param(value: Any) -> bool:
    """
    Determines if a value is in short-form (direct value) or full-form (V1Param dict).

    A value is considered "short-form" if it's NOT a dict containing V1Param keys.

    Examples of short-form values:
        - 32 (int)
        - "adam" (str)
        - 0.8 (float)
        - [1, 2, 3] (list)
        - {"key1": "val1", "key2": "val2"} (dict without V1Param keys)

    Examples of full-form values:
        - {} (empty dict - treated as full-form for backward compatibility)
        - {"value": 32}
        - {"value": "outputs.path", "ref": "ops.upstream"}
        - {"value": "data.csv", "toInit": True}

    Args:
        value: The value to check

    Returns:
        True if the value is in short-form, False if it's a full-form V1Param dict
    """
    if not isinstance(value, Mapping):
        # Non-dict values are always short-form
        return True

    # Empty dict is treated as full-form for backward compatibility
    # (passing {} means "no value specified", not "value is empty dict")
    if not value:
        return False

    # A dict is short-form if it has NO V1Param keys
    return not bool(V1_PARAM_KEYS & set(value.keys()))


def normalize_param_value(value: Any) -> Dict:
    """
    Normalizes a param value to full-form V1Param dict.

    If the value is already in full-form, returns it as-is.
    If the value is in short-form, wraps it in {"value": <value>}.

    Args:
        value: The value to normalize (can be short-form or full-form)

    Returns:
        A dict suitable for V1Param.from_dict()
    """
    if value is None:
        return {"value": None}

    if is_short_form_param(value):
        return {"value": value}

    return value


def validate_param_value(value, ref):
    if ref and not isinstance(value, str):
        raise ValueError(
            "Value must be of type string when a ref is provided, received `{}` instead.".format(
                value
            )
        )


class ParamValueMixin:
    @property
    def is_literal(self):
        raise NotImplementedError

    @property
    def is_ref(self):
        raise NotImplementedError

    @property
    def is_template_ref(self):
        raise NotImplementedError

    @property
    def is_join_ref(self):
        raise NotImplementedError

    @property
    def is_runs_ref(self):
        raise NotImplementedError

    @property
    def is_ops_ref(self):
        raise NotImplementedError

    @property
    def is_dag_ref(self):
        raise NotImplementedError

    def validate(self):
        validate_param_value(
            value=self.value,
            ref=self.ref,
        )

    @property
    def entity_value(self) -> Optional[str]:
        if not self.is_ref:
            return None
        return ctx_refs.get_entity_value(self.value)

    @property
    def entity_type(self) -> Optional[str]:
        if not self.is_ref:
            return None
        return ctx_refs.get_entity_type(self.value)

    @property
    def searchable_ref(self) -> str:
        if not self.is_ref or self.is_join_ref:
            return ""
        return "{}.{}".format(self.ref, ctx_refs.parse_ref_value(self.value))

    def get_spec(
        self,
        name: str,
        iotype: str,
        is_flag: bool,
        is_list: bool,
        is_context: bool,
        arg_format: str,
    ):
        """
        Checks if the value is param ref and validates it.

        returns: ParamSpec or None
        raises: ValidationError
        """
        if not self.is_literal and not (
            self.is_join_ref and isinstance(self.value, Mapping)
        ):
            # value validation is the same for search and ref
            value_parts = PARAM_REGEX.search(self.value)
            if value_parts:
                value_parts = value_parts.group(1).strip()
            else:
                value_parts = self.value

            value_parts = [s.strip() for s in value_parts.split(".")]
            if len(value_parts) > 3:
                raise PolyaxonValidationError(
                    "Could not parse value `{}` for param `{}`.".format(
                        self.value, name
                    )
                )
            if len(value_parts) == 1 and value_parts[0] not in ctx_sections.CONTEXTS:
                raise PolyaxonValidationError(
                    "Received an invalid value `{}` for param `{}`. "
                    "Value must be one of `{}`".format(
                        self.value, name, ctx_sections.CONTEXTS
                    )
                )
            # Check the case of current DAG, it should not allow to use outputs
            if (
                len(value_parts) == 1
                and self.is_dag_ref
                and value_parts[0] == ctx_sections.OUTPUTS
            ):
                raise PolyaxonValidationError(
                    "Received an invalid value `{}` for param `{}`. "
                    "You can not use `{}` of current dag".format(
                        self.value, name, ctx_sections.OUTPUTS
                    )
                )
            if (
                len(value_parts) == 2
                and value_parts[0] not in ctx_sections.CONTEXTS_WITH_NESTING
            ):
                raise PolyaxonValidationError(
                    "Received an invalid value `{}` for param `{}`. "
                    "Value `{}` must be one of `{}`".format(
                        self.value,
                        name,
                        value_parts[0],
                        ctx_sections.CONTEXTS_WITH_NESTING,
                    )
                )
            if len(value_parts) == 3 and value_parts[0] != ctx_sections.ARTIFACTS:
                raise PolyaxonValidationError(
                    "Received an invalid value `{}` for param `{}`. "
                    "Value `{}` must can only be equal to `{}`".format(
                        self.value, name, value_parts[0], ctx_sections.ARTIFACTS
                    )
                )
        if self.is_ref:
            if self.is_join_ref:
                if not is_context and not is_list and iotype != types.ARTIFACTS:
                    raise PolyaxonValidationError(
                        "Param `{}` has a an input type `{}`, "
                        "it does not expect a list of values from the join. "
                        "You should either pass a single value or add `isList` "
                        "to you IO definition".format(
                            name,
                            iotype,
                        )
                    )
            else:
                ctx_refs.validate_ref(ref=self.ref, name=name)

        return ParamSpec(
            name=name,
            type=iotype,
            param=self,
            is_flag=is_flag,
            is_list=is_list,
            is_context=is_context,
            is_requested=True,
            arg_format=arg_format,
        )


class V1Param(BaseSchemaModel, ctx_refs.RefMixin, ParamValueMixin):
    """Params can provide values to inputs/outputs.

    Params can be passed in several ways
     * literal values that the user sets manually.
     * a reference from a previous run, in which case
       Polyaxon will validate during the compilation time if the user who initiated the run
       has access to that organization/project/run.
     * a reference from an upstream operation in the context of a DAG.


    When a param is passed from the CLI or directly in the YAML/Python specification,
    it will be validated against the [inputs/outputs](/docs/core/specification/io/)
    defined in the [component](/docs/core/specification/component/)

    Args:
        value: any
        ref: str, optional
        context_only: bool, optional
        connection: str, optional
        to_init: bool, optional
        to_env: str, optional

    ## YAML usage

    Polyaxon supports two syntaxes for defining params: **short-form** and **full-form**.

    ### Short-form syntax

    > **N.B**: Requires Polyaxon CLI version `>= 2.13`

    For simple literal values, you can use the concise short-form syntax:

    ```yaml
    >>> params:
    >>>   loss: MeanSquaredError
    >>>   preprocess: true
    >>>   accuracy: 0.1
    >>>   batch_size: 32
    >>>   layers: [64, 128, 256]
    >>>   config:
    >>>     optimizer: adam
    >>>     lr: 0.001
    ```

    ### Full-form syntax

    The full-form syntax is required when using advanced features like `ref`, `toInit`, `toEnv`, `connection`, or `contextOnly`:

    ```yaml
    >>> params:
    >>>   loss:
    >>>     value: MeanSquaredError
    >>>   preprocess:
    >>>     value: true
    >>>   accuracy:
    >>>     value: 0.1
    >>>   outputs_path:
    >>>     ref: ops.upstream-job1
    >>>     value: outputs.images_path
    ```

    You can mix both syntaxes in the same params section:

    ```yaml
    >>> params:
    >>>   # Short-form for simple values
    >>>   batch_size: 32
    >>>   learning_rate: 0.001
    >>>   # Full-form when using refs or other options
    >>>   upstream_output:
    >>>     ref: ops.training
    >>>     value: outputs.model_path
    >>>   data_path:
    >>>     value: /data/train
    >>>     toInit: true
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Param
    >>> params = {
    >>>     "loss": V1Param(value="MeanSquaredError"),
    >>>     "preprocess": V1Param(value=True),
    >>>     "accuracy": V1Param(value=0.1),
    >>>     "outputs-path": V1Param(ref="ops.upstream_job1", value="outputs.images_path")
    >>> }
    ```

    ## Fields

    ### value

    The value to pass, if no `ref` is passed then it corresponds to a literal value,
    and will be validated eagerly.
    Otherwise it will be a future validation during the compilation time.

    ```yaml
    >>> params:
    >>>   loss:
    >>>     value: MeanSquaredError
    >>>   learning_rate:
    >>>     value: 0.001
    ```

    The value could be coming from the [context](/docs/core/context/), for example:

    ```yaml
    >>> params:
    >>>   current_project:
    >>>     value: {{globals.project_name}}
    >>>   current_run:
    >>>     value: {{globals.uuid}}
    >>>   fully_resolved_artifacts_path:
    >>>     value: {{globals.run_artifacts_path}}
    >>>   fully_resolved_artifacts_outputs_path:
    >>>     value: {{globals.run_outputs_path}}
    ```

    Resolving values from the IO (inputs/outputs) of the reference:

    ```yaml
    >>>   specific_input:
    >>>     value: {{inputs.input_name}}
    >>>   specific_outputs:
    >>>     value: {{outputs.output_name}}
    >>>   all_inputs_dict:
    >>>     value: {{inputs}}
    >>>   all_outputs_dict:
    >>>     value: {{outputs}}
    >>>   specific_input:
    >>>     value: {{inputs.input_name}}
    >>>   specific_outputs:
    >>>     value: {{outputs.output_name}}
    ```

    Resolving paths from the artifacts and lineages of the reference:

    ```yaml
    >>>   run_artifacts_subpath_without_context:
    >>>     value: {{artifacts}}
    >>>   run_artifacts_outputs_subpath_without_context:
    >>>     value: {{artifacts.outputs}}
    >>>   run_path_of_lineage:
    >>>     value: {{artifacts.lineage_name}}
    >>>   run_tensorboard_path_from_lineage:
    >>>     value: {{artifacts.tensorboard}}
    >>>   run_tensorboard_path_from_lineage:
    >>>     value: {{artifacts.tensorboard}}
    ```

    Resolving artifacts manually from the reference based on the
    [ArtifactsType](/docs/core/specification/types/#v1artifactstype)

    ```yaml
    >>>   files_and_dirs:
    >>>     value:
    >>>       - files: ["subpath/file1", "another/subpath/file2.ext"]
    >>>       - dirs: ["subpath/dir1", "another/subpath/dir2"]
    ```

    > **Note**: the difference between using `artifacts.lineage_name`
    > and [ArtifactsType](/docs/core/specification/types/#v1artifactstype),
    > is that the former will only expose the path based on any lineage logged during the runtime,
    > the later is a manual way of selecting specific files and dirs.

    ### ref

    Ref corresponds to a reference of an object.

    A reference could be a previous run in the database or
    an operation in DAG that has not been executed yet.

    ```yaml
    >>> params:
    >>>   loss:
    >>>     value: outputs.loss
    >>>     ref: ops.upstream-job-1
    ```

    ```yaml
    >>> params:
    >>>   loss:
    >>>     value: outputs.loss
    >>>     ref: runs.fcc462d764104eb698d3cca509f34154
    ```

    ### contextOnly

    A flag to signal to Polyaxon that this param should not be validated
    against the inputs/outputs, and it's only used to resolve some
    information and inject it into the context.

    ```yaml
    >>> params:
    >>>   convolutions:
    >>>     contextOnly: true
    >>>     value:
    >>>       conv1:
    >>>          kernels: [32, 32]
    >>>          size: [2, 2]
    >>>          strides: [1, 1]
    >>>       conv2:
    >>>          kernels: [64, 64]
    >>>          size: [2, 2]
    >>>          strides: [1, 1]
    ```

    Polyaxon will not check if this param was required by an input/output,
    and will inject it automatically in the context to be used.
    You can use for example `{{ convolutions.conv1 }}` in the specification.

    ### connection

    A connection to use with the parameter.
    if the initial Input/Output definition has a predefined connection and this connection
    is provided, it will override the that value and will be added to the context.

    ### toInit

    if True the param will be converted to an init container.

    For example, to initialize some artifacts without using the
    [init section](/docs/core/specification/init/), you can use `toInit` to turn an artifacts value
    or git value to an init container:

    ```yaml
    >>>   files_and_dirs:
    >>>     toInit: true
    >>>     value:
    >>>       - files: ["subpath/file1", "another/subpath/file2.ext"]
    >>>       - dirs: ["subpath/dir1", "another/subpath/dir2"]
    ```

    ### toEnv

    > **N.B**: Requires Polyaxon CLI and Polyaxon Agent/CE version `>= 1.12`

    If passed, it will be converted automatically to an environment variable.

    ```yaml
    >>> param1:
    >>>   toEnv: ENV_VAR_NAME_TO_USE
    >>>   value: "some value"
    ```
    """

    _IDENTIFIER = "param"

    value: Optional[Any] = None
    ref: Optional[StrictStr] = None
    context_only: Optional[bool] = Field(alias="contextOnly", default=False)
    connection: Optional[StrictStr] = None
    to_init: Optional[bool] = Field(alias="toInit", default=None)
    to_env: Optional[StrictStr] = Field(alias="toEnv", default=None)

    @field_validator("ref")
    @skip_partial
    def check_ref(cls, ref, values):
        values = cls.get_data_from_values(values)
        validate_param_value(value=cls.get_value_for_key("value", values), ref=ref)
        return ref

    @classmethod
    def read(
        cls, values: Any, partial: bool = False, config_type: str = None
    ) -> "V1Param":
        """Create a V1Param, supporting both short-form and full-form.

        Short-form allows simple literal values without the verbose `value:` wrapper:
            - 32 (int)
            - "adam" (str)
            - [1, 2, 3] (list)
            - {"key": "val"} (dict without V1Param keys)

        Full-form requires explicit V1Param fields:
            - {"value": 32}
            - {"value": "outputs.path", "ref": "ops.upstream"}
            - {"value": "data.csv", "toInit": True}

        Args:
            values: The value to convert (short-form or full-form)
            partial: If True, skip validation
            config_type: Optional config type for reading

        Returns:
            V1Param instance
        """
        normalized = normalize_param_value(values)
        return super().read(normalized, partial=partial, config_type=config_type)


class ParamSpec(
    namedtuple(
        "ParamSpec",
        "name type param is_flag is_list is_context is_requested arg_format",
    )
):
    def get_typed_param_value(self):
        if self.type == "str":
            if self.is_list:
                value = self.param.value or []  # Handles the case of None
                return [to_string(v) for v in value]
            return to_string(self.param.value)
        return self.param.value

    def get_display_value(self):
        if self.is_flag:
            return "--{}".format(self.name) if self.param.value else ""
        return self.get_typed_param_value()

    def __repr__(self):
        value = self.get_display_value()
        if value is None:
            return ""
        return to_string(value)

    def as_str(self):
        return str(self)

    def as_arg(self):
        if self.arg_format:
            from polyaxon._polyaxonfile.specs.libs.parser import PolyaxonfileParser

            return (
                PolyaxonfileParser.parse_expression(
                    self.arg_format, {self.name: self.get_typed_param_value()}
                )
                if self.param.value is not None
                else ""
            )
        if self.is_flag:
            return "--{}".format(self.name) if self.param.value else ""
        return (
            "--{}={}".format(self.name, self.as_str())
            if self.param.value is not None
            else ""
        )

    def to_parsed_param(self):
        parsed_param = {
            "connection": self.param.connection,
            "value": self.get_typed_param_value(),
            "type": self.type,
            "as_str": self.as_str(),
            "as_arg": self.as_arg(),
        }
        return parsed_param

    def validate_to_init(self) -> bool:
        if not self.param.to_init:
            return False

        if not self.type:
            raise PolyaxonValidationError(
                "Param `{}` cannot be turned to an initializer without a valid type! "
                "Please set an input with a type to use the `to_init` field.".format(
                    self.name
                )
            )

        if self.param.connection:
            return True

        if self.type in {types.GIT, types.ARTIFACTS, types.DOCKERFILE}:
            return True

        raise PolyaxonValidationError(
            "Param `{}` with type `{}`, "
            "cannot be turned to an init container automatically.".format(
                self.name, self.type
            )
        )

    def to_init(self) -> Optional[V1Init]:
        if not self.param.to_init:
            return None
        if self.type == types.GIT:
            return V1Init.from_dict(
                dict(git=self.param.value, connection=self.param.connection)
            )
        elif self.type == types.DOCKERFILE:
            return V1Init.from_dict(
                dict(dockerfile=self.param.value, connection=self.param.connection)
            )
        elif self.type == types.ARTIFACTS:
            return V1Init.from_dict(
                dict(artifacts=self.param.value, connection=self.param.connection)
            )
        elif self.type == types.PATH:
            paths = to_list(self.param.value, check_none=True)
            return V1Init.from_dict(dict(paths=paths, connection=self.param.connection))
        elif self.param.connection:
            return V1Init(connection=self.param.connection)
        return None

    def validate_ref(
        self,
        context: Optional[Dict],
        is_template: bool = False,
        check_all_refs: bool = False,
    ):
        """
        Given a param reference to an operation, we check that the operation exists in the context,
        and that the types
        """
        if self.param.is_join_ref:
            if not self.is_list and self.type != types.ARTIFACTS:
                raise PolyaxonValidationError(
                    "Param `{}` has a an input type `{}`"
                    "and it does not expect a list of values from the join".format(
                        self.name,
                        self.param.value,
                    )
                )
            return

        if (
            is_template
            or self.param.is_template_ref
            or (self.param.is_runs_ref and not check_all_refs)
        ):
            return

        context = context or {}

        if self.param.searchable_ref not in context:
            # Artifacts can be logged during runtime
            if self.param.entity_type == types.ARTIFACTS:
                return
            raise PolyaxonValidationError(
                "Param `{}` has a ref value `{}`, "
                "but reference with name `{}` has no such information, "
                "please check that your polyaxonfile defines the correct template".format(
                    self.name, self.param.value, self.param.ref
                )
            )

        if not types.are_compatible(self.type, context[self.param.searchable_ref].type):
            raise PolyaxonValidationError(
                "Param `{}` has a an input type `{}` "
                "and it does not correspond to the type of the value `{}` "
                "received from `{}` with type `{}`".format(
                    self.name,
                    self.type,
                    self.param.value,
                    self.param.ref,
                    context[self.param.searchable_ref].type,
                )
            )

        if self.is_list != context[self.param.searchable_ref].is_list:
            raise PolyaxonValidationError(
                "Param `{}` has a an input type List[`{}`]"
                "and it does not correspond to the output value `{}` received from `{}`".format(
                    self.name, self.type, self.param.value, self.param.ref
                )
            )
