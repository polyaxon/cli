from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, List, Optional, Union
from typing_extensions import Annotated, Literal

from clipped.compact.pydantic import Field, StrictStr, root_validator, validator
from clipped.config.schema import skip_partial
from clipped.types.numbers import StrictIntOrFloat
from clipped.types.ref_or_obj import RefField

from polyaxon import types
from polyaxon._flow.matrix.enums import V1HPKind
from polyaxon._schemas.base import BaseSchemaModel

if TYPE_CHECKING:
    from clipped.compact.pydantic import CallableGenerator

try:
    import numpy as np
except (ImportError, ModuleNotFoundError):
    np = None


# pylint:disable=redefined-outer-name


def validate_pchoice(values):
    dists = [v for v in values if v]
    if sum(dists) > 1:
        raise ValueError("The distribution of different outcomes should sum to 1.")


class PChoice(tuple):
    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if isinstance(value, (list, tuple)) and len(value) == 2:
            if isinstance(value[1], float) and 0 <= value[1] < 1:
                return value
        raise ValueError("This field expects a list of [value<Any>, dist<float>].")


def _validate_range(
    value: List, required_keys: List, keys: List, check_order: bool = True
):
    # TODO: Fix error message
    if len(value) < len(required_keys):
        raise ValueError(
            "This field expects a list of {} or {} elements, received {}.".format(
                len(required_keys), len(keys), len(value)
            )
        )
    # Check that lower value is smaller than higher value
    if check_order and value[0] >= value[1]:
        raise ValueError(
            "{key2} value must be strictly higher that {key1} value, "
            "received instead {key1}: {val1}, {key2}: {val2}".format(
                key1=required_keys[0],
                key2=required_keys[1],
                val1=value[0],
                val2=value[1],
            )
        )
    if len(required_keys) == 3 and not value[2]:
        raise ValueError(
            "{} must be > 0, received {}".format(required_keys[2], value[2])
        )


class BaseRange(BaseSchemaModel):
    _REQUIRED_KEYS = []
    _OPTIONAL_KEYS = []
    _CHECK_ORDER = True

    @root_validator
    def validate_range(cls, values):
        value = list(values.values())
        _validate_range(
            value,
            cls._REQUIRED_KEYS,
            cls._REQUIRED_KEYS + cls._OPTIONAL_KEYS,
            check_order=cls._CHECK_ORDER,
        )
        return values


class Range(BaseRange):
    start: Union[float]
    stop: Union[float]
    step: StrictIntOrFloat
    _REQUIRED_KEYS = ["start", "stop", "step"]


class RangeStr(StrictStr):
    _CLASS = Range

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def validate(cls, value: str):
        if not isinstance(value, str) or ":" not in value:
            raise ValueError("This field expects a string of values separated by `:`.")
        keys = cls._CLASS._REQUIRED_KEYS + cls._CLASS._OPTIONAL_KEYS
        if value:
            value = value.split(":")
            return cls._CLASS(**dict(zip(keys, value)))
        raise ValueError(
            "`{}` requires `{}` or `{}` elements, received `{}`".format(
                cls._CLASS.__name__,
                len(cls._CLASS._REQUIRED_KEYS),
                len(keys),
                len(value),
            )
        )


class RangeList(list):
    _CLASS = Range

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.validate

    @classmethod
    def validate(cls, value: List):
        if not isinstance(value, list):
            raise ValueError("This field expects a list of values.")
        keys = cls._CLASS._REQUIRED_KEYS + cls._CLASS._OPTIONAL_KEYS
        if value:
            return cls._CLASS(**dict(zip(keys, value)))
        raise ValueError(
            "`{}` requires `{}` or `{}` elements, received `{}`".format(
                cls._CLASS.__name__,
                len(cls._CLASS._REQUIRED_KEYS),
                len(keys),
                len(value),
            )
        )


class DateRange(Range):
    start: date
    stop: date
    step: int


class DateRangeList(RangeList):
    _CLASS = DateRange


class DateTimeRange(Range):
    start: datetime
    stop: datetime
    step: timedelta


class DateTimeRangeList(RangeList):
    _CLASS = DateTimeRange


class Space(BaseRange):
    start: Union[float]
    stop: Union[float]
    num: int
    _REQUIRED_KEYS = ["start", "stop", "num"]


class LinSpace(Space):
    pass


class LinSpaceList(RangeList):
    _CLASS = LinSpace


class LinSpaceStr(RangeStr):
    _CLASS = LinSpace


class GeomSpace(Space):
    pass


class GeomSpaceList(RangeList):
    _CLASS = GeomSpace


class GeomSpaceStr(RangeStr):
    _CLASS = GeomSpace


class LogSpace(Space):
    base: Optional[int]
    _OPTIONAL_KEYS = ["base"]


class LogSpaceList(RangeList):
    _CLASS = LogSpace


class LogSpaceStr(RangeStr):
    _CLASS = LogSpace


class Dist(BaseRange):
    low: Union[float]
    high: Union[float]
    size: Optional[int]
    _REQUIRED_KEYS = ["low", "high"]
    _OPTIONAL_KEYS = ["size"]
    _CHECK_ORDER = False


class QDist(BaseRange):
    low: Union[float]
    high: Union[float]
    q: StrictIntOrFloat
    size: Optional[int]
    _REQUIRED_KEYS = ["low", "high", "q"]
    _OPTIONAL_KEYS = ["size"]
    _CHECK_ORDER = False


class Uniform(Dist):
    pass


class UniformList(RangeList):
    _CLASS = Uniform


class UniformStr(RangeStr):
    _CLASS = Uniform


class QUniform(QDist):
    pass


class QUniformList(RangeList):
    _CLASS = QUniform


class QUniformStr(RangeStr):
    _CLASS = QUniform


class LogUniform(Dist):
    pass


class LogUniformList(RangeList):
    _CLASS = LogUniform


class LogUniformStr(RangeStr):
    _CLASS = LogUniform


class QLogUniform(QDist):
    pass


class QLogUniformList(RangeList):
    _CLASS = QLogUniform


class QLogUniformStr(RangeStr):
    _CLASS = QLogUniform


class Normal(BaseRange):
    loc: Union[float]
    scale: Union[float]
    size: Optional[int]
    _REQUIRED_KEYS = ["loc", "scale"]
    _OPTIONAL_KEYS = ["size"]
    _CHECK_ORDER = False


class NormalList(RangeList):
    _CLASS = Normal


class NormalStr(RangeStr):
    _CLASS = Normal


class QNormal(BaseRange):
    loc: Union[float]
    scale: Union[float]
    q: StrictIntOrFloat
    size: Optional[int]
    _REQUIRED_KEYS = ["loc", "scale", "q"]
    _OPTIONAL_KEYS = ["size"]
    _CHECK_ORDER = False


class QNormalList(RangeList):
    _CLASS = QNormal


class QNormalStr(RangeStr):
    _CLASS = QNormal


class LogNormal(Normal):
    pass


class LogNormalList(RangeList):
    _CLASS = LogNormal


class LogNormalStr(RangeStr):
    _CLASS = LogNormal


class QLogNormal(QNormal):
    pass


class QLogNormalList(RangeList):
    _CLASS = QLogNormal


class QLogNormalStr(RangeStr):
    _CLASS = QLogNormal


def validate_matrix(values):
    v = sum(map(lambda x: 1 if x else 0, values))
    if v == 0 or v > 1:
        raise ValueError(
            "Matrix element is not valid, one and only one option is required."
        )


class BaseHpParamConfig(BaseSchemaModel):
    _USE_DISCRIMINATOR = True

    @staticmethod
    def validate_io(io: "V1IO"):  # noqa
        if io.type not in ["int", "float"]:
            raise ValueError(
                "Param `{}` has a an input type `{}` "
                "and it does not correspond to hyper-param type `int or float`.".format(
                    io.name,
                    io.type,
                )
            )
        return True


class V1HpChoice(BaseHpParamConfig):
    """`Choice` picks a value from a of list values.

    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: choice
    >>>     value: [1, 2, 3, 4, 5]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpChoice
    >>> param_test = V1HpChoice(value=[1, 2, 3, 4, 5])
    ```
    """

    _IDENTIFIER = V1HPKind.CHOICE

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[List[Any], RefField]]

    @staticmethod
    def validate_io(io: "V1IO"):  # noqa
        return True

    @property
    def is_distribution(self):
        return False

    @property
    def is_continuous(self):
        return False

    @property
    def is_discrete(self):
        return True

    @property
    def is_range(self):
        return False

    @property
    def is_categorical(self):
        return any(
            [
                v
                for v in self.value
                if not isinstance(v, (int, float, complex, np.integer, np.floating))
            ]
        )

    @property
    def is_uniform(self):
        return False


class V1HpPChoice(BaseHpParamConfig):
    """`PChoice` picks a value with a probability from a list of
    [(value, probability), (value, probability), ...].

    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: pchoice
    >>>     value: [(1, 0.1), (2, 0.1), (3, 0.8)]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpPChoice
    >>> param_test = V1HpPChoice(value=[("A", 0.1), ("B", 0.1), ("C", 0.8)])
    ```
    """

    _IDENTIFIER = V1HPKind.PCHOICE

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[List[PChoice], RefField]]

    @validator("value")
    @skip_partial
    def validate_value(cls, value):
        if value and isinstance(value, (list, tuple)):
            validate_pchoice(values=[v[1] for v in value if v])

        return value

    @staticmethod
    def validate_io(io: "V1IO"):  # noqa
        return True

    @property
    def is_distribution(self):
        return True

    @property
    def is_continuous(self):
        return False

    @property
    def is_discrete(self):
        return True

    @property
    def is_range(self):
        return False

    @property
    def is_categorical(self):
        return False

    @property
    def is_uniform(self):
        return False


class V1HpRange(BaseHpParamConfig):
    """`Range` picks a value from a generated list of values using `[start, stop, step]`,
    you can pass values in these forms:
      * [1, 10, 2]
      * {start: 1, stop: 10, step: 2}
      * '1:10:2'

    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: range
    >>>     value: [1, 10, 2]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpRange
    >>> param_test = V1HpRange(value=[1, 10, 2])
    ```
    """

    _IDENTIFIER = V1HPKind.RANGE

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[Range, RangeList, RangeStr, RefField]]

    @property
    def is_distribution(self):
        return False

    @property
    def is_continuous(self):
        return False

    @property
    def is_discrete(self):
        return True

    @property
    def is_range(self):
        return True

    @property
    def is_categorical(self):
        return False

    @property
    def is_uniform(self):
        return False


class V1HpDateRange(BaseHpParamConfig):
    """`DateRange` picks a value from a generated list of values using `[start, stop, step]`,
    you can pass values in these forms:
      * `["2019-06-24", "2019-06-25", 3600 * 24]`
      * `{start: "2019-06-24 00:00", stop: "2019-06-28 00:00", step: 1}`

    **Step (frequency)**: represents a timedelta in days.

    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: daterange
    >>>     value: ["2019-06-22", "2019-07-25", 1]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpDateRange
    >>> param_test = V1HpDateRange(value=["2019-06-22", "2019-06-25", 2])
    ```
    """

    _IDENTIFIER = V1HPKind.DATERANGE

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[DateRange, DateRangeList, RefField]]

    @staticmethod
    def validate_io(io: "V1IO"):  # noqa
        if io.type != types.DATE:
            raise ValueError(
                "Param `{}` has a an input type `{}` "
                "and it does not correspond to hyper-param type `date`.".format(
                    io.name,
                    io.type,
                )
            )
        return True

    @property
    def is_distribution(self):
        return False

    @property
    def is_continuous(self):
        return False

    @property
    def is_discrete(self):
        return True

    @property
    def is_range(self):
        return True

    @property
    def is_categorical(self):
        return False

    @property
    def is_uniform(self):
        return False


class V1HpDateTimeRange(BaseHpParamConfig):
    """`DateTimeRange` picks a value from a generated list of values using `[start, stop, step]`,
    you can pass values in these forms:
      * `["2019-06-24T21:20:07+02:00", "2019-06-25T21:20:07+02:00", 3600]`
      * `{start: "2019-06-24 00:00", stop: "2019-06-28 00:00", step: 3600 * 4}`

    **Step (frequency)**: represents a timedelta in seconds.

    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: datetimerange
    >>>     value: ["2019-06-22 21:00", "2019-06-25 21:00", 3600]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpDateTimeRange
    >>> param_test = V1HpDateTimeRange(value=["2019-06-22 21:00", "2019-06-25 21:00", 3600])
    ```
    """

    _IDENTIFIER = V1HPKind.DATETIMERANGE

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[DateTimeRange, DateTimeRangeList, RefField]]

    @staticmethod
    def validate_io(io: "V1IO"):  # noqa
        if io.type != types.DATETIME:
            raise ValueError(
                "Param `{}` has a an input type `{}` "
                "and it does not correspond to hyper-param type `datetime`.".format(
                    io.name,
                    io.type,
                )
            )
        return True

    @property
    def is_distribution(self):
        return False

    @property
    def is_continuous(self):
        return False

    @property
    def is_discrete(self):
        return True

    @property
    def is_range(self):
        return True

    @property
    def is_categorical(self):
        return False

    @property
    def is_uniform(self):
        return False


class V1HpLinSpace(BaseHpParamConfig):
    """`LinSpace` picks a value from a generated list of steps from start to stop spaced evenly
    on a linear scale `[start, stop, step]`, you can pass values in these forms:
      * [1, 10, 20]
      * {start: 1, stop: 10, num: 20}
      * '1:10:20'

    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: linspace
    >>>     value: [1, 10, 20]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpLinSpace
    >>> param_test = V1HpLinSpace(value=[1, 10, 20])
    ```
    """

    _IDENTIFIER = V1HPKind.LINSPACE

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[LinSpace, LinSpaceList, LinSpaceStr, RefField]]

    @property
    def is_distribution(self):
        return False

    @property
    def is_continuous(self):
        return False

    @property
    def is_discrete(self):
        return True

    @property
    def is_range(self):
        return True

    @property
    def is_categorical(self):
        return False

    @property
    def is_uniform(self):
        return False


class V1HpLogSpace(BaseHpParamConfig):
    """`LogSpace` picks a value from a generated list of steps from start to stop spaced evenly
    on a log scale `[start, stop, step]` or `[start, stop, step, base]`,
    where `base` is optional with 10 as default value,
    you can pass values in these forms:
      * [1, 10, 20]
      * [1, 10, 20, 2]
      * {start: 1, stop: 10, num: 20}
      * {start: 1, stop: 10, num: 20, base: 2}
      * '1:10:20:2'

    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: logspace
    >>>     value: [1, 10, 20]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpLogSpace
    >>> param_test = V1HpLinSpace(value=[1, 10, 20])
    ```
    """

    _IDENTIFIER = V1HPKind.LOGSPACE

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[LogSpace, LogSpaceList, LogSpaceStr, RefField]]

    @property
    def is_distribution(self):
        return False

    @property
    def is_continuous(self):
        return False

    @property
    def is_discrete(self):
        return True

    @property
    def is_range(self):
        return True

    @property
    def is_categorical(self):
        return False

    @property
    def is_uniform(self):
        return False


class V1HpGeomSpace(BaseHpParamConfig):
    """`GeomSpace` picks a value from a generated list of steps from start to stop spaced evenly
    on a geometric progression `[start, stop, step]`, you can pass values in these forms:
      * [1, 10, 20]
      * {start: 1, stop: 10, num: 20}
      * '1:10:20'

    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: geomspace
    >>>     value: [1, 10, 20]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpGeomSpace
    >>> param_test = V1HpGeomSpace(value=[1, 10, 20])
    ```
    """

    _IDENTIFIER = V1HPKind.GEOMSPACE

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[GeomSpace, GeomSpaceList, GeomSpaceStr, RefField]]

    @property
    def is_distribution(self):
        return False

    @property
    def is_continuous(self):
        return False

    @property
    def is_discrete(self):
        return True

    @property
    def is_range(self):
        return True

    @property
    def is_categorical(self):
        return False

    @property
    def is_uniform(self):
        return False


class V1HpUniform(BaseHpParamConfig):
    """`Uniform` draws samples from a uniform distribution over the half-open
    interval `[low, high)`, you can pass values in these forms:
      * 0:1
      * [0, 1]
      * {'low': 0, 'high': 1}

    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: uniform
    >>>     value: [0, 1]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpUniform
    >>> param_test = V1HpUniform(value=[0, 1])
    ```
    """

    _IDENTIFIER = V1HPKind.UNIFORM

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[Uniform, UniformList, UniformStr, RefField]]

    @property
    def is_distribution(self):
        return True

    @property
    def is_uniform(self):
        return True

    @property
    def is_continuous(self):
        return True

    @property
    def is_discrete(self):
        return False

    @property
    def is_range(self):
        return False

    @property
    def is_categorical(self):
        return False


class V1HpQUniform(BaseHpParamConfig):
    """`QUniform` samples from a quantized uniform distribution over `[low, high]`
    (`round(uniform(low, high) / q) * q`),
    you can pass values in these forms:
      * 0:1:0.1
      * [0, 1, 0.1]
      * {'low': 0, 'high': 1, 'q': 0.1}


    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: quniform
    >>>     value: [0, 1, 0.1]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpQUniform
    >>> param_test = V1HpQUniform(value=[0, 1, 0.1])
    ```
    """

    _IDENTIFIER = "quniform"

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[QUniform, QUniformList, QUniformStr, RefField]]

    @property
    def is_distribution(self):
        return True

    @property
    def is_uniform(self):
        return False

    @property
    def is_continuous(self):
        return True

    @property
    def is_discrete(self):
        return False

    @property
    def is_range(self):
        return False

    @property
    def is_categorical(self):
        return False


class V1HpLogUniform(BaseHpParamConfig):
    """`LogUniform` samples from a log uniform distribution over`[low, high]`,
    you can pass values in these forms:
      * 0:1
      * [0, 1]
      * {'low': 0, 'high': 1}


    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: loguniform
    >>>     value: [0, 1]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpLogUniform
    >>> param_test = V1HpLogUniform(value=[0, 1])
    ```
    """

    _IDENTIFIER = V1HPKind.LOGUNIFORM

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[LogUniform, LogUniformList, LogUniformStr, RefField]]

    @property
    def is_distribution(self):
        return True

    @property
    def is_uniform(self):
        return False

    @property
    def is_continuous(self):
        return True

    @property
    def is_discrete(self):
        return False

    @property
    def is_range(self):
        return False

    @property
    def is_categorical(self):
        return False


class V1HpQLogUniform(BaseHpParamConfig):
    """`LogUniform` samples from a log uniform distribution over`[low, high]`,
    you can pass values in these forms:
      * 0:1:0.1
      * [0, 1, 0.1]
      * {'low': 0, 'high': 1, 'q': 0.1}


    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: qloguniform
    >>>     value: [0, 1, 0.1]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpQLogUniform
    >>> param_test = V1HpQLogUniform(value=[0, 1, 0.1])
    ```
    """

    _IDENTIFIER = V1HPKind.QLOGUNIFORM

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[QLogUniform, QLogUniformList, QLogUniformStr, RefField]]

    @property
    def is_distribution(self):
        return True

    @property
    def is_uniform(self):
        return False

    @property
    def is_continuous(self):
        return True

    @property
    def is_discrete(self):
        return False

    @property
    def is_range(self):
        return False

    @property
    def is_categorical(self):
        return False

    @property
    def min(self):
        return None


class V1HpNormal(BaseHpParamConfig):
    """`Normal` draws random samples from a normal (Gaussian) distribution defined by
    `[loc, scale]`, you can pass values in these forms:
      * 0:1
      * [0, 1]
      * {'loc': 0, 'scale': 1}


    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: normal
    >>>     value: [0, 1]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpNormal
    >>> param_test = V1HpNormal(value=[0, 1])
    ```
    """

    _IDENTIFIER = V1HPKind.NORMAL

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[Normal, NormalList, NormalStr, RefField]]

    @property
    def is_distribution(self):
        return True

    @property
    def is_uniform(self):
        return False

    @property
    def is_continuous(self):
        return True

    @property
    def is_discrete(self):
        return False

    @property
    def is_range(self):
        return False

    @property
    def is_categorical(self):
        return False


class V1HpQNormal(BaseHpParamConfig):
    """`QNormal` draws random samples from a quantized normal (Gaussian) distribution defined by
    `[loc, scale]`, you can pass values in these forms:
      * 0:1:0.1
      * [0, 1, 0.1]
      * {'loc': 0, 'scale': 1, 'q': 0.1}


    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: qnormal
    >>>     value: [0, 1, 0.1]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpQNormal
    >>> param_test = V1HpNormal(value=[0, 1, 0.1])
    ```
    """

    _IDENTIFIER = V1HPKind.QNORMAL

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[QNormal, QNormalList, QNormalStr, RefField]]

    @property
    def is_distribution(self):
        return True

    @property
    def is_uniform(self):
        return False

    @property
    def is_continuous(self):
        return True

    @property
    def is_discrete(self):
        return False

    @property
    def is_range(self):
        return False

    @property
    def is_categorical(self):
        return False


class V1HpLogNormal(BaseHpParamConfig):
    """`LogNormal` draws random samples from a log normal (Gaussian) distribution defined by
    `[loc, scale]`, you can pass values in these forms:
      * 0:1
      * [0, 1]
      * {'loc': 0, 'scale': 1}


    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: lognormal
    >>>     value: [0, 1]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpLogNormal
    >>> param_test = V1HpLogNormal(value=[0, 1])
    ```
    """

    _IDENTIFIER = V1HPKind.LOGNORMAL

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[LogNormal, LogNormalList, LogNormalStr, RefField]]

    @property
    def is_distribution(self):
        return True

    @property
    def is_uniform(self):
        return False

    @property
    def is_continuous(self):
        return True

    @property
    def is_discrete(self):
        return False

    @property
    def is_range(self):
        return False

    @property
    def is_categorical(self):
        return False


class V1HpQLogNormal(BaseHpParamConfig):
    """`QLogNormal` draws random samples from a log normal (Gaussian) distribution defined by
    `[loc, scale]`, you can pass values in these forms:
      * 0:1:0.1
      * [0, 1, 0.1]
      * {'loc': 0, 'scale': 1, 'q': 0.1}


    ```yaml
    >>> params:
    >>>   paramTest:
    >>>     kind: qlognormal
    >>>     value: [0, 1, 0.1]
    ```

    ```python
    >>> from polyaxon.schemas import V1HpQLogNormal
    >>> param_test = V1HpQLogNormal(value=[0, 1])
    ```
    """

    _IDENTIFIER = V1HPKind.QLOGNORMAL

    kind: Literal[_IDENTIFIER] = _IDENTIFIER
    value: Optional[Union[QLogNormal, QLogNormalList, QLogNormalStr, RefField]]

    @property
    def is_distribution(self):
        return True

    @property
    def is_uniform(self):
        return False

    @property
    def is_continuous(self):
        return True

    @property
    def is_discrete(self):
        return False

    @property
    def is_range(self):
        return False

    @property
    def is_categorical(self):
        return False


V1HpParam = Annotated[
    Union[
        V1HpChoice,
        V1HpPChoice,
        V1HpRange,
        V1HpDateRange,
        V1HpDateTimeRange,
        V1HpLinSpace,
        V1HpLogSpace,
        V1HpGeomSpace,
        V1HpUniform,
        V1HpQUniform,
        V1HpLogUniform,
        V1HpQLogUniform,
        V1HpNormal,
        V1HpQNormal,
        V1HpLogNormal,
        V1HpQLogNormal,
    ],
    Field(discriminator="kind"),
]
