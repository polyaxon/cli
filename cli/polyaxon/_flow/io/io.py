import re

from typing import Any, Dict, List, Optional, Union

from clipped.compact.pydantic import Field, StrictStr, root_validator, validator
from clipped.config.schema import skip_partial
from clipped.types.numbers import StrictIntOrFloat
from clipped.types.ref_or_obj import BoolOrRef, IntOrRef, RefField

from polyaxon._config.parser import ConfigParser
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon.exceptions import PolyaxonSchemaError, PolyaxonValidationError

IO_NAME_BLACK_LIST = ["globals", "params", "connections"]
IO_NAME_ERROR = (
    "Received an input/output with a name in {}, "
    "please use a different name that does "
    "not already taken by the context".format(IO_NAME_BLACK_LIST)
)


def validate_io_value(
    name: str,
    type: str,
    value: Any,
    default: Any,
    is_optional: bool,
    is_list: bool,
    validation: Optional[Union["V1Validation", Dict]],
    parse: bool = True,
):
    try:
        parsed_value = ConfigParser.parse(type)(
            key=name,
            value=value,
            is_list=is_list,
            is_optional=is_optional,
            default=default,
        )
        if validation:
            validation.run_validation(
                value=parsed_value, type=type, is_optional=is_optional
            )
        if parse:
            return parsed_value
        # Return the original value, the parser will return specs sometimes
        if value is not None:
            return value
        return default
    except PolyaxonSchemaError as e:
        raise PolyaxonValidationError(
            "Could not parse value `%s` for `%s`, an error was encountered: %s"
            % (value, name, e)
        )


def validate_io(
    name: str,
    type: str,
    value: Any,
    is_optional: bool,
    is_list: bool,
    is_flag: bool,
    validation: Optional[Union["V1Validation", Dict]],
):
    if type and value:
        try:
            value = validate_io_value(
                name=name,
                type=type,
                value=value,
                default=None,
                is_list=is_list,
                is_optional=is_optional,
                validation=validation,
            )
        except PolyaxonValidationError as e:
            raise ValueError(e)

    if not is_optional and value:
        raise ValueError(
            "IO `{}` is not optional and has default value `{}`. "
            "Please either make it optional or remove the default value.".format(
                name, value
            )
        )

    if is_flag and type != "bool":
        raise TypeError(
            "IO type `{}` cannot be a flag, it must be of type `{}`".format(
                type, "bool"
            )
        )

    return value


class V1Validation(BaseSchemaModel):
    """Validation is used to validate inputs/outputs.

    Validation is defined as a sdt of predicates, each one of the predicates that must be satisfied.

    Args:
        delay: bool, optional
        gt: int, optional
        ge: int, optional
        lt: int, optional
        le: int, optional
        multiple_of: int, optional
        min_items: int, optional
        max_digits: int, optional
        decimal_places: int, optional
        regex: str, optional
        min_length: int, optional
        max_length: int, optional
        keys: List[str], optional
        contains_keys: List[str], optional
        excludes_keys: List[str], optional
        contains: List[str], optional
        excludes: List[str], optional
        options: List[str], optional

    ## YAML usage

    ```yaml
    >>> inputs:
    >>>   - name: loss
    >>>     type: str
    >>>     validation:
    >>>       options: [MeanSquaredError, MeanAbsoluteError]
    >>>   - name: learning_rate
    >>>     type: float
    >>>     validation:
    >>>       gt: 0.001
    >>>       lt: 0.5
    >>> options:
    >>>   - name: accuracy
    >>>     type: float
    >>>     validation:
    >>>       ge: 0.5
    >>>   - name: outputs-path
    >>>     type: path
    >>>     validation:
    >>>       regex: "^s3://(?P<bucket>[a-z0-9-.]{3,63})/(?P<key>.+)$"
    ```

    ## Python usage

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1Validation
    >>> inputs = [
    >>>     V1IO(
    >>>         name="loss",
    >>>         type='str',
    >>>         validation=[V1Validation(options=["MeanSquaredError", "MeanAbsoluteError"])]
    >>>     ),
    >>>     V1IO(
    >>>         name="learning_rate",
    >>>         type='float',
    >>>         validation=[V1Validation(gt=0.001, lt=0.5)]
    >>> ]
    >>> outputs = [
    >>>     V1IO(
    >>>         name="accuracy",
    >>>         type='float',
    >>>         validation=[V1Validation(ge=0.5)]
    >>>     ),
    >>>     V1IO(
    >>>         name="outputs-path",
    >>>         type=types.PATH,
    >>>         validation=[V1Validation(regex="^s3://(?P<bucket>[a-z0-9-.]{3,63})/(?P<key>.+)$")]
    >>>     )
    >>> ]
    ```

    ## Validation

    ### Delay

    To instruct the parser to only validate the input/output at compilation or resolution time:

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    >>>     description: A short description about this input
    >>>     type: float
    >>>     value: 1.1
    >>>     validation:
    >>>       delay: true
    ```

    This flag is enabled by default for outputs, since they can only be
    resolved after or during the run. To request validation at compilation time for outputs,
    you need to set this flag to `False`.

    ### Validators

    #### Numerical Constraints

    > these constraints are also applied item wise for lists and for dict values

    * gt - greater than
    * lt - less than
    * ge - greater than or equal to
    * le - less than or equal to
    * multipleOf - a multiple of the given number

    #### Decimal Constraints

    > these constraints are also applied item wise for lists and for dict values

    * minDigits - minimum number of digits
    * maxDigits - maximum number of digits
    * decimalPlaces - maximum number of decimal places

    #### String Constraints

    > these constraints are also applied item wise for lists and for dict values

    * regex - a regex pattern
    * minLength - minimum length
    * maxLength - maximum length

    #### Generic Constraints

    > these constraints are also applied item wise for lists and for dict values

    * contains - a list of values that must be present
    * excludes - a list of values that must not be present
    * options - a list of values that must be present

    #### Dict Constraints
    * keys - a list of keys that must be present in the dict
    * containsKeys - a list of keys that must be present in the dict
    * excludesKeys - a list of keys that must not be present in the dict

    #### Items Constraints

    * minItems - minimum number of items
    * maxItems - maximum number of items
    """

    delay: Optional[BoolOrRef]
    gt: Optional[Union[StrictIntOrFloat, RefField]]
    ge: Optional[Union[StrictIntOrFloat, RefField]]
    lt: Optional[Union[StrictIntOrFloat, RefField]]
    le: Optional[Union[StrictIntOrFloat, RefField]]
    multiple_of: Optional[Union[StrictIntOrFloat, RefField]] = Field(alias="multipleOf")
    min_digits: Optional[IntOrRef] = Field(alias="minDigits")
    max_digits: Optional[IntOrRef] = Field(alias="maxDigits")
    decimal_places: Optional[IntOrRef] = Field(alias="decimalPlaces")
    regex: Optional[StrictStr]
    min_length: Optional[IntOrRef] = Field(alias="minLength")
    max_length: Optional[IntOrRef] = Field(alias="maxLength")
    contains: Optional[Any]
    excludes: Optional[Any]
    options: Optional[Any]
    min_items: Optional[IntOrRef] = Field(alias="minItems")
    max_items: Optional[IntOrRef] = Field(alias="maxItems")
    keys: Optional[Union[List[StrictStr], RefField]]
    contains_keys: Optional[Union[List[StrictStr], RefField]] = Field(
        alias="containsKeys"
    )
    excludes_keys: Optional[Union[List[StrictStr], RefField]] = Field(
        alias="excludesKeys"
    )

    def _validate_gt(self, value):
        if self.gt is not None and value <= self.gt:
            raise PolyaxonValidationError(
                f"Value `{value}` must be greater than `{self.gt}`"
            )

    def _validate_ge(self, value):
        if self.ge is not None and value < self.ge:
            raise PolyaxonValidationError(
                f"Value `{value}` must be greater than or equal to `{self.ge}`"
            )

    def _validate_lt(self, value):
        if self.lt is not None and value >= self.lt:
            raise PolyaxonValidationError(
                f"Value `{value}` must be less than `{self.lt}`"
            )

    def _validate_le(self, value):
        if self.le is not None and value > self.le:
            raise PolyaxonValidationError(
                f"Value `{value}` must be less than or equal to `{self.le}`"
            )

    def _validate_multiple_of(self, value):
        if self.multiple_of is not None and value % self.multiple_of != 0:
            raise PolyaxonValidationError(
                f"Value `{value}` must be a multiple of `{self.multiple_of}`"
            )

    def _validate_min_digits(self, value):
        if (
            self.min_digits is not None
            and len(str(value).replace(".", "")) < self.min_digits
        ):
            raise PolyaxonValidationError(
                f"Value `{value}` must have at least `{self.min_digits}` digits"
            )

    def _validate_max_digits(self, value):
        if (
            self.max_digits is not None
            and len(str(value).replace(".", "")) > self.max_digits
        ):
            raise PolyaxonValidationError(
                f"Value `{value}` must have at most `{self.max_digits}` digits"
            )

    def _validate_decimal_places(self, value):
        if (
            self.decimal_places is not None
            and len(str(value).split(".")[1]) > self.decimal_places
        ):
            raise PolyaxonValidationError(
                f"Value `{value}` must have at most `{self.decimal_places}` decimal places"
            )

    def _validate_regex(self, value):
        if self.regex is not None and not re.match(self.regex, value):
            raise PolyaxonValidationError(
                f"Value `{value}` must match the regex `{self.regex}`"
            )

    def _validate_min_length(self, value):
        if self.min_length is not None and len(value) < self.min_length:
            raise PolyaxonValidationError(
                f"Value `{value}` must have at least `{self.min_length}` characters"
            )

    def _validate_max_length(self, value):
        if self.max_length is not None and len(value) > self.max_length:
            raise PolyaxonValidationError(
                f"Value `{value}` must have at most `{self.max_length}` characters"
            )

    def _validate_contains(self, value):
        if self.contains is not None and self.contains not in value:
            raise PolyaxonValidationError(
                f"Value `{value}` must contain one of the values `{self.contains}`"
            )

    def _validate_excludes(self, value):
        if self.excludes is not None and self.excludes in value:
            raise PolyaxonValidationError(
                f"Value `{value}` must not contain any of the values `{self.excludes}`"
            )

    def _validate_options(self, value):
        if self.options is not None and value not in self.options:
            raise PolyaxonValidationError(
                f"Value `{value}` must be one of the values `{self.options}`"
            )

    def _validate_min_items(self, value):
        if self.min_items is not None and len(value) < self.min_items:
            raise PolyaxonValidationError(
                f"Value `{value}` must have at least `{self.min_items}` items"
            )

    def _validate_max_items(self, value):
        if self.max_items is not None and len(value) > self.max_items:
            raise PolyaxonValidationError(
                f"Value `{value}` must have at most `{self.max_items}` items"
            )

    def _validate_keys(self, value):
        if self.keys is not None and set(value.keys()) != set(self.keys):
            raise PolyaxonValidationError(
                f"Value `{value}` must contain all the keys `{self.keys}`"
            )

    def _validate_contains_keys(self, value):
        if self.contains_keys is not None and not all(
            k in value for k in self.contains_keys
        ):
            raise PolyaxonValidationError(
                f"Value `{value}` must contain all the keys `{self.contains_keys}`"
            )

    def _validate_excludes_keys(self, value):
        if self.excludes_keys is not None and any(
            k in value for k in self.excludes_keys
        ):
            raise PolyaxonValidationError(
                f"Value `{value}` must not contain any of the keys `{self.excludes_keys}`"
            )

    def run_validation(
        self,
        value: Any,
        type: str,
        is_optional: bool,
    ):
        if value is None and is_optional:
            return

        def _validate_value(v):
            self._validate_gt(v)
            self._validate_ge(v)
            self._validate_lt(v)
            self._validate_le(v)
            self._validate_multiple_of(v)
            self._validate_min_digits(v)
            self._validate_max_digits(v)
            self._validate_decimal_places(v)
            self._validate_regex(v)
            self._validate_min_length(v)
            self._validate_max_length(v)
            self._validate_contains(v)
            self._validate_excludes(v)
            self._validate_options(v)

        if isinstance(value, (list, tuple, set)):
            for v in value:
                _validate_value(v)
        elif isinstance(value, dict):
            for v in value.values():
                _validate_value(v)
        else:
            _validate_value(value)

        if isinstance(value, (list, tuple, set, dict)):
            self._validate_min_items(value)
            self._validate_max_items(value)

        if isinstance(value, dict):
            self._validate_keys(value)
            self._validate_contains_keys(value)
            self._validate_excludes_keys(value)


class V1IO(BaseSchemaModel):
    """Each Component may have its own inputs and outputs.
    The inputs and outputs describe the expected parameters to pass to the component
    and their types. In the context of a DAG,
    inputs and outputs types are used to validate the flow of information
    going from one operation to another.

    The final value of an input/output can be resolved
    from [params](/docs/core/specification/params/), or from other values in
    the [context](/docs/core/context/).

    Examples:
     * A build component may have a git repository as input and a container image as output.
     * A training component may have a container image, data path,
       and some hyperparameters as input and a list of metrics and artifacts as outputs.

    An input/output section includes a name, a description, a type to check the value passed,
    a flag to tell if the input/output is optional, and a default value if it's optional.

    Sometimes users prefer to pass a param to the `command` or `args`
    section only if the value is not null. Polyaxon provides a way to do that using
    `{{ params.PARAM_NAME.as_arg }}`,
    this will be empty if the value is null or `--PARAM_NAME=value` if the value is not null.
    If the value is of type bool, it will be `--PARAM_NAME`.
    It's also possible to control how the param should be
    converted to an argument using the `arg_format`.

    To learn how to pass valid values,
    please check the [param section](/docs/core/specification/params/).

    Args:
        name: str
        description: str, optional
        type: str, any python type hint, pydantic built-in types, and gcs, s3, wasb, dockerfile, git, image, event, artifacts, path, metric, metadata, date, datetime.
        value: any, optional
        is_optional: bool, optional (**Deprecated**)
        is_list: bool, optional
        is_flag: bool, optional
        arg_format: str, optional
        connection: str, optional
        to_init: bool, optional
        to_env: str, optional
        validation: [V1Validation](/docs/core/specification/validation/), optional
        delay_validation: bool, optional (**Deprecated**: please see valiation.delay)
        options: List[any], optional (**Deprecated**: please see valiation)

    ## YAML usage

    ```yaml
    >>> inputs:
    >>>   - name: loss
    >>>     type: str
    >>>     isOptional: true
    >>>     value: MeanSquaredError
    >>>   - name: preprocess
    >>>     type: bool
    >>> outputs:
    >>>   - name: accuracy
    >>>     type: float
    >>>   - name: outputs-path
    >>>     type: path
    ```

    ## Python usage

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1IO
    >>> inputs = [
    >>>     V1IO(
    >>>         name="loss",
    >>>         type='str',
    >>>         description="Loss to use for training my model",
    >>>         is_optional=True,
    >>>         value="MeanSquaredError"
    >>>     ),
    >>>     V1IO(
    >>>         name="preprocess",
    >>>         type='bool',
    >>>         description="A flag to preprocess data before training",
    >>>     )
    >>> ]
    >>> outputs = [
    >>>     V1IO(
    >>>         name="accuracy",
    >>>         type='float',
    >>>     ),
    >>>     V1IO(
    >>>         name="outputs-path",
    >>>         type=types.PATH,
    >>>     )
    >>> ]
    ```

    These inputs/outputs declarations can be used to pass values to our program:

    ```bash
     ... --loss={{ loss }} {{ params.preprocess.as_arg }}
    ```

    ## Fields

    ### name

    The input/output name. The name must be a valid slug, and cannot include dots `.`.

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    ```

    ### description

    An optional description for the input/output.

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    >>>     description: A short description about this input
    ```

    ### type

    The type of the input/output. The type will be used to validate the value

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    >>>     description: A short description about this input
    >>>     type: float
    ```

    for more details about composite type validation and schema,
    please check the [types section](/docs/core/specification/types/),
    possible types include any python type hint, pydantic built-in types, and:
        * URI: "uri"
        * LIST: "list"
        * GCS: "gcs"
        * S3: "s3"
        * WASB: "wasb"
        * DOCKERFILE: "dockerfile"
        * GIT: "git"
        * IMAGE: "image"
        * EVENT: "event"
        * ARTIFACTS: "artifacts"
        * PATH: "path"
        * METRIC: "metric"
        * METADATA: "metadata"

    ### value

    If an input is optional you should assign it a value.
    If an output is optional you can assign it a value.

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    >>>     description: A short description about this input
    >>>     type: float
    >>>     value: 1.1
    ```

    ### isOptional

    A flag to tell if an input/output is optional.

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    >>>     description: A short description about this input
    >>>     type: float
    >>>     value: 1.1
    >>>     isOptional: true
    ```

    ### isList

    > **Deprecated**: Please use `type: List[TYPING]` instead.

    In `v2` you should:

    ```yaml
    >>> inputs:
    >>>   - name: learning_rates
    >>>     type: List[float]
    ```

    A flag used in `v1` to tell if an input/output is a list of the type passed.

    ```yaml
    >>> inputs:
    >>>   - name: learning_rates
    >>>     type: float
    >>>     isList: true
    ```

    In this case the input name `learning_rates` will expect a value of type `List[float]`,
    e.g. [0.1 0.01, 0.0001]

    ### argFormat

    A key to control how to convert an input/output to a CLI argument if the value is not null,
    the default behavior:

     * For bool type: If the resolved value of the input is True,
       `"{{ params.PARAM_NAME.as_arg }}"` will be resolved to `"--PARAM_NAME"`
       otherwise it will be an empty string `""`.
     * For non-bool types: If the resolved value of the input is not null,
       `"{{ params.PARAM_NAME.as_arg }}"` will be resolved to `"--PARAM_NAME=value"`
       otherwise it will be an empty string `""`.

    Let's look at the flowing example:

    ```yaml
    >>> inputs:
    >>>   - name: lr
    >>>     type: float
    >>>   - name: check
    >>>     type: bool
    ```

    **This manifest**:

    ```yaml
    >>> container:
    >>>    command: ["{{ lr }}", "{{ check }}"]
    ```

    Will be transformed to:

    ```yaml
    >>> container:
    >>>    command: ["0.01", "true"]
    ```

    **This manifest**:

    ```yaml
    >>> container:
    >>>    command: ["{{ params.lr.as_arg }}", "{{ params.check.as_arg }}"]
    ```

    Will be transformed to:

    ```yaml
    >>> container:
    >>>    command: ["--lr=0.01", "--check"]
    ```

    Changing the behavior with `argFormat`:

    ```yaml
    >>> inputs:
    >>>   - name: lr
    >>>     type: float
    >>>     argFormat: "lr={{ lr }}"
    >>>   - name: check
    >>>     type: bool
    >>>     argFormat: "{{ 1 if check else 0 }}"
    ```

    **This manifest**:

    ```yaml
    >>> container:
    >>>    command: ["{{ params.lr.as_arg }}", "{{ params.check.as_arg }}"]
    ```

    Will be transformed to:

    ```yaml
    >>> container:
    >>>    command: ["lr=0.01", "1"]
    ```

    ### connection

    A connection to use with the input/outputs.

    ### toInit

    If True, it will be converted to an init container.

    ### toEnv

    > **N.B**: Requires Polyaxon CLI and Polyaxon Agent/CE version `>= 1.12`

    If passed, it will be converted automatically to an environment variable.

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    >>>     type: float
    >>>     value: 1.1
    >>>     toEnv: MY_LEARNING_RATE
    ```

    ### validation [v2]

    A schema to use to validate the input/output value or to delay the validation to runtime.

    To instruct the parser to only validate the input/output at compilation or resolution time:

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    >>>     description: A short description about this input
    >>>     type: float
    >>>     value: 1.1
    >>>     validation:
    >>>       delay: true
    ```

    This flag is enabled by default for outputs, since they can only be
    resolved after or during the run. To request validation at compilation time for outputs,
    you need to set this flag to `False`.

    To validate an input/output value:

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    >>>     description: A short description about this input
    >>>     type: float
    >>>     value: 1.1
    >>>     validation:
    >>>       min: 0.01
    >>>       max: 0.1
    ```

    Options allow to pass a list of values that will be used to validate any passed params.

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    >>>     description: A short description about this input
    >>>     type: float
    >>>     value: 0.1
    >>>     validation:
    >>>       options: [0.1, 0.2, 0.3]
    ```

    ### delayValidation

    > **Deprecated**: Please use `validation: ...` instead.

    A flag to tell if an input/output should not be
    validated at compilation or resolution time.

    This flag is enabled by default for outputs, since they can only be
    resolved after or during the run. To request validation at compilation time for outputs,
    you need to set this flag to `False`.


    ### options

    > **Deprecated**: Please use `validation: ...` instead.

    Options allow to pass a list of values that will be used to validate any passed params.

    ```yaml
    >>> inputs:
    >>>   - name: learning_rate
    >>>     description: A short description about this input
    >>>     type: float
    >>>     value: 1.1
    >>>     options: [1.1, 2.2, 3.3]
    ```

    If you pass the value `4.4` for the learning rate it will raise a validation error.

    ## Example


    ```yaml
    >>> version: 1.1
    >>> kind: component
    >>> inputs:
    >>>   - name: batch_size
    >>>     description: batch size
    >>>     isOptional: true
    >>>     value: 128
    >>>     type: int
    >>>   - name: num_steps
    >>>     isOptional: true
    >>>     default: 500
    >>>     type: int
    >>>   - name: learning_rate
    >>>     isOptional: true
    >>>     default: 0.001
    >>>     type: float
    >>>   - name: dropout
    >>>     isOptional: true
    >>>     default: 0.25
    >>>     type: float
    >>>   - name: num_epochs
    >>>     isOptional: true
    >>>     default: 1
    >>>     type: int
    >>>   - name: activation
    >>>     isOptional: true
    >>>     default: relu
    >>>     type: str
    >>> run:
    >>>   kind: job
    >>>   image: foo:bar
    >>>   container:
    >>>     command: [python3, model.py]
    >>>     args: [
    >>>         "--batch_size={{ batch_size }}",
    >>>         "--num_steps={{ num_steps }}",
    >>>         "--learning_rate={{ learning_rate }}",
    >>>         "--dropout={{ dropout }",
    >>>         "--num_epochs={{ num_epochs }}",
    >>>         "--activation={{ activation }}"
    >>>     ]
    ```

    ### Running a typed component using the CLI

    Using the Polyaxon CLI we can now run this component and override the inputs' default values:

    ```bash
    polyaxon run -f polyaxonfile.yaml -P activation=sigmoid -P dropout=0.4
    ```

    This will generate a manifest and will replace the params passed and validated against the inputs' types.

    ### Required inputs

    In the example all inputs are optional.
    If we decide for instance to make the activation required:

    ````yaml
    >>> ...
    >>> inputs:
    >>>   ...
    >>>   - name: activation
    >>>     type: str
    >>>   ...
    ...
    ````

    By changing this input, polyaxon can not run this component without passing the activation:


    ```bash
    polyaxon run -f polyaxonfile.yaml -P activation=sigmoid
    ```
    """

    _IDENTIFIER = "io"

    name: StrictStr
    description: Optional[StrictStr]
    type: Optional[StrictStr]
    is_optional: Optional[bool] = Field(alias="isOptional")
    is_list: Optional[bool] = Field(alias="isList")
    is_flag: Optional[bool] = Field(alias="isFlag")
    arg_format: Optional[StrictStr] = Field(alias="argFormat")
    connection: Optional[StrictStr]
    to_init: Optional[bool] = Field(alias="toInit")
    to_env: Optional[StrictStr] = Field(alias="toEnv")
    value: Optional[Any]
    validation: Optional[V1Validation]
    delay_validation: Optional[bool] = Field(alias="delayValidation")
    options: Optional[Any]

    @validator("name", always=True)
    def validate_name(cls, v):
        if v in IO_NAME_BLACK_LIST:
            raise ValueError(IO_NAME_ERROR)
        return v

    @root_validator(pre=True)
    def handle_validation(cls, values):
        validation = values.get("validation")
        if not validation and (
            values.get("options") is not None
            or values.get("delay_validation") is not None
        ):
            validation = {}
        if isinstance(validation, dict):
            validation = V1Validation(**validation)
        if values.get("options") is not None:
            validation.options = values.pop("options")
        if values.get("delay_validation") is not None:
            validation.delay = values.pop("delay_validation")
        if validation:
            values["validation"] = validation
        return values

    @root_validator
    @skip_partial
    def validate_io(cls, values):
        validate_io(
            name=values.get("name"),
            type=values.get("type"),
            value=values.get("value"),
            is_list=values.get("is_list"),
            is_optional=values.get("is_optional"),
            is_flag=values.get("is_flag"),
            validation=values.get("validation"),
        )
        return values

    def validate_value(self, value: Any, parse: bool = True):
        if self.type is None:
            return value

        return validate_io_value(
            name=self.name,
            type=self.type,
            value=value,
            default=self.value,
            is_list=self.is_list,
            is_optional=self.is_optional,
            validation=self.validation,
            parse=parse,
        )

    def get_repr_from_value(self, value):
        """A string representation that is used to create hash cache"""
        value = self.validate_value(value=value, parse=False)
        io_dict = self.to_light_dict(include_attrs=["name", "type"])
        io_dict["value"] = value
        return io_dict

    def get_repr(self):
        """A string representation that is used to create hash cache"""
        io_dict = self.to_light_dict(include_attrs=["name", "type", "value"])
        return io_dict
