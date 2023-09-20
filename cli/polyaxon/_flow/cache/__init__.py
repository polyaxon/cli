from typing import List, Optional, Union

from clipped.compact.pydantic import StrictStr
from clipped.types.ref_or_obj import BoolOrRef, IntOrRef, RefField

from polyaxon._flow.cache.enums import CacheSection
from polyaxon._schemas.base import BaseSchemaModel


class V1Cache(BaseSchemaModel):
    """Polyaxon provides a caching layer for operation executions,
    this behavior is enabled by default for all runs executed in the context of a DAG,
    a hyperparameter tuning, or a mapping.

    When runs are cached their outputs will be reused for future
    runs with similar inputs and component version.

    Args:
        disable: bool, optional, default: False
        ttl: int, optional
        io: List[str], optional
        sections: List[str], optional

    ## YAML usage

    ```yaml
    >>> cache:
    >>>   disable:
    >>>   ttl:
    >>>   inputs:
    >>>   sections:
    ```

    ## Python usage

    ```python
    >>> from polyaxon.schemas import V1Cache
    >>> cache = V1Cache(
    >>>   disable=False,
    >>>   ttl=3600,
    >>>   io=['param1', 'param4']
    >>>   sections=['init']
    >>> )
    ```

    ## Fields

    ### disable

    Caching is enabled by default, if you want to disable the cache
    for a component or just for a specific component run, you can set this field to `false`

    ```yaml
    >>> cache:
    >>>   disable: true
    ```

    ### ttl

    the default caching behavior is to persist and reuse a run's results everytime a new operation
    with similar characteristics is scheduled to run.

    In order to invalidate the cache after a certain period of time you can
    define a time to live value.

    ```yaml
    >>> cache:
    >>>   ttl: 36000  # 10 hours
    ```

    ### io

    You may want to discard an input/output from being considered for
    the cache state calculation,
    or you may want to cache a component's run irrespective of the params you pass to some io.

    This field gives you full control to define how you want to calculate the cache state.

    ```yaml
    >>> cache:
    >>>   io: ['param1', 'param4']
    ```

    ### sections

    By default the cache manager will consider the state of the `init`, `connections`,
    and `containers` (command and args) to trigger the cache hit logic.
    You may want to discard a section from being considered for
    the cache state calculation.

    This field gives you allows to define the sections that should be used
    to calculate the cache state.

    ```yaml
    >>> cache:
    >>>   sections: ['containers']
    ```
    """

    _IDENTIFIER = "cache"

    disable: Optional[BoolOrRef]
    ttl: Optional[IntOrRef]
    io: Optional[Union[List[StrictStr], RefField]]
    sections: Optional[Union[List[CacheSection], RefField]]
