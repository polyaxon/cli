from typing import Dict, Optional, Union

from clipped.compact.pydantic import StrictStr
from clipped.types.ref_or_obj import IntOrRef, RefField

from polyaxon._flow.params.params import ParamValueMixin, V1Param
from polyaxon._schemas.base import BaseSchemaModel


class V1JoinParam(V1Param, ParamValueMixin):
    _IDENTIFIER = "join_param"

    @property
    def is_literal(self):
        return False

    @property
    def is_ref(self):
        return True

    @property
    def is_template_ref(self):
        return False

    @property
    def is_join_ref(self):
        return True

    @property
    def is_runs_ref(self):
        return False

    @property
    def is_ops_ref(self):
        return False

    @property
    def is_dag_ref(self):
        return False


class V1Join(BaseSchemaModel):
    """Joins allow to query several runs based on a search specification.

    The result of the join will be a list of values based on the results from executing the search.

    A Join corresponds to a valid [query specification](/docs/core/query-language/),
    the result of the search will be used to resolve
    the params defined in the join.

    ```yaml
    >>> joins:
    >>>   - query: "metrics.loss: <0.01"
    >>>     sort: "metrics.loss"
    >>>     limit: 5
    >>>     params:
    >>>       all_param1:
    >>>         value: inputs.param1
    >>>       all_result1:
    >>>         value: outputs.result1
    >>>       all_result2:
    >>>         value: outputs.result2
    >>>       tensorboard_paths:
    >>>         value: artifacts.tensorboard
    >>>         contextOnly: true
    >>>   - query: "metrics.accuracy: >.9"
    >>>     sort: "-metrics.accuracy"
    >>>     params:
    >>>       all_inputs:
    >>>         value: inputs
    >>>       all_outputs:
    >>>         value: outputs
    >>>       run_artifact_paths:
    >>>         value: artifacts.base
    >>>       uuids:
    >>>         value: globals.uuid
    >>>         contextOnly: true
    >>>       files:
    >>>         value: {files: ["subpath/files", "subpath2/file2"]}
    >>>         toInit: true
    ```

    ```python
    >>> joins = [
    >>>     V1Join(
    >>>         query="metrics.loss: <0.01",
    >>>         sort="metrics.loss",
    >>>         limit=5,
    >>>         params={
    >>>             "all_param1": V1JoinParam(value="inputs.param1"),
    >>>             "all_result1": V1JoinParam(value="outputs.result1"),
    >>>             "all_result2": V1JoinParam(value="outputs.result2"),
    >>>             "tensorboard_paths": V1JoinParam(
    >>>                 value="artifacts.tensorboard", context_only=True
    >>>             ),
    >>>         },
    >>>     ),
    >>>     V1Join(
    >>>         query="metrics.accuracy: >.9",
    >>>         sort="-metrics.accuracy",
    >>>         params={
    >>>             "all_inputs": V1JoinParam(value="inputs"),
    >>>             "all_outputs": V1JoinParam(value="outputs"),
    >>>             "run_artifact_paths": V1JoinParam(value="artifacts")
    >>>             "uuids": V1JoinParam(value="globals.uuid"),
    >>>             "artifacts": V1JoinParam(
    >>>                 value={files: ["subpath/files", "subpath2/file2"]},
    >>>                 to_init=True,
    >>>             ),
    >>>         }
    >>>     )
    >>> ]
    ```

    This will instruct Polyaxon to perform 2 searches.
    Each search will expose the params to be used similar to the default
    [params section](/docs/core/specification/params/).
    Polyaxon will validate the params of search against the IO(inputs/outputs) definition.
    Users should make sure that their IO definition specify the `isList: true`,
    unless the type is `artifacts`.

    If a param is based on `contexts`, `inputs`, `outputs`, or `artifacts`
    Polyaxon will turn that param into a list by querying
    that field from all runs in the search result:

    ```python
    >>>  {
    >>>     "all_param1": [val_run_1, val_run_223, val_run_234, ...],
    >>>     ...
    >>> }
    ```

    When the param is of type [ArtifactsType](/docs/core/specification/types/#v1artifactstype),
    all files and dirs will be concatenated in a single list,
    each value will be prefixed with the uuid (run path) of each run in the query result:

    ```python
    >>>  {
    >>>     "artifacts": {
    >>>         "file": [
    >>>             "run_3/subpath/files", "run_3/subpath2/file2",
    >>>             "run_4/subpath/files", "run_4/subpath2/file2",
    >>>             ...
    >>>         ],
    >>>     }
    >>>     ...
    >>> }
    ```

    > **Note**: the difference between using `artifacts.lineage_name`
    > and [ArtifactsType](/docs/core/specification/types/#v1artifactstype),
    > is that the former will only expose the path(s) based on any lineage logged
    > during the runtime, the later is a manual way of selecting specific files and dirs.

    ## Fields

    ### query

    A valid query respecting
    [Polyaxon Query Language](/docs/core/query-language/runs/#query)

    ```yaml
    >>> joins:
    >>>   - query: "metrics.loss: <0.01, project.name: {{ globals.project_name}}, kind: job"
    ```

    ### sort

    A valid sort respecting
    [Polyaxon Query Language](/docs/core/query-language/runs/#sort)

    ```yaml
    >>> joins:
    >>>   - sort: "created_at, -metrics.loss"
    ```

    ### limit

    The maximum number of runs to join based on the query/sort condition.

    > **Note**: at the moment we have a hard limit, `5000`, on the number of upstream runs to join.

    ```yaml
    >>> joins:
    >>>   - limit: "10"
    ```

    ### offset

    ```yaml
    >>> joins:
    >>>   - offset: "100"
    ```

    An optional integer used for pagination.

    ### params

    Similar to the default [params specification](/docs/core/specification/params/)
    with the exception that it does not accept the `ref` key.
    The reference is generated automatically based on the search performed by Polyaxon.

    The fields supported: `value`, `context_only`, `connection`, `to_init`
    """

    _IDENTIFIER = "join"

    ref: Optional[StrictStr] = None
    query: StrictStr
    sort: Optional[StrictStr] = None
    limit: Optional[IntOrRef] = None
    offset: Optional[IntOrRef] = None
    params: Optional[Union[Dict[str, V1JoinParam], RefField]] = None
