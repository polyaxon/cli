from clipped.types.gcs import GcsPath as _GcsPath
from clipped.types.s3 import S3Path as _S3Path
from clipped.types.uri import Uri as _Uri
from clipped.types.wasb import WasbPath as _WasbPath


class GcsPath(_GcsPath):
    """GCS type.

    Args:
        bucket: str
        blob: str

    ### YAML usage

    The inputs definition

    ```yaml
    >>> inputs:
    >>>   - name: test1
    >>>     type: gcs
    >>>   - name: test2
    >>>     type: gcs
    ```

    The params usage

    ```yaml
    >>> params:
    >>>   test1: {value: "gs://bucket1"}
    >>>   test1: {value: "gs://bucket2/blobName"}
    ```

    ### Python usage

    The inputs definition

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1IO
    >>> inputs = [
    >>>     V1IO(
    >>>         name="test1",
    >>>         type=types.GCS,
    >>>     ),
    >>>     V1IO(
    >>>         name="test2",
    >>>         type=types.GCS,
    >>>     ),
    >>> ]
    ```

    The params usage

    ```python
    >>> from polyaxon.schemas import V1Param
    >>> params = {
    >>>     "test1": V1Param(value="gs://bucket1"),
    >>>     "test2": V1Param(value="gs://bucket1/blobName")),
    >>> }
    ```
    """


class S3Path(_S3Path):
    """S3 type.

    Args:
        bucket: str
        key: str

    ### YAML usage

    The inputs definition

    ```yaml
    >>> inputs:
    >>>   - name: test1
    >>>     type: s3
    >>>   - name: test2
    >>>     type: s3
    ```

    The params usage

    ```yaml
    >>> params:
    >>>   test1: {value: "s3://bucket1"}
    >>>   test1: {value: "s3://bucket2/keyName"}}
    ```

    ### Python usage

    The inputs definition

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1IO
    >>> inputs = [
    >>>     V1IO(
    >>>         name="test1",
    >>>         type=types.S3,
    >>>     ),
    >>>     V1IO(
    >>>         name="test2",
    >>>         type=types.S3,
    >>>     ),
    >>> ]
    ```

    The params usage

    ```python
    >>> from polyaxon.schemas import V1Param
    >>> params = {
    >>>     "test1": V1Param(value="s3://bucket1"),
    >>>     "test2": V1Param(value="s3://bucket1/keyName"),
    >>> }
    ```
    """


class WasbPath(_WasbPath):
    """Wasb type.

    Args:
        container: str
        storage_account: str
        path: str

    ### YAML usage

    The inputs definition

    ```yaml
    >>> inputs:
    >>>   - name: test1
    >>>     type: wasb
    >>>   - name: test2
    >>>     type: wasb
    ```

    The params usage

    ```yaml
    >>> params:
    >>>   test1: {value: "wasbs://container@user.blob.core.windows.net/path"}
    >>>   test2: {value: "wasbs://container@user.blob.core.windows.net/path"}
    ```

    ### Python usage

    The inputs definition

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1IO
    >>> inputs = [
    >>>     V1IO(
    >>>         name="test1",
    >>>         type=types.WASB,
    >>>     ),
    >>>     V1IO(
    >>>         name="test2",
    >>>         type=types.WASB,
    >>>     ),
    >>> ]
    ```

    The params usage

    ```python
    >>> from polyaxon.schemas import V1Param
    >>> params = {
    >>>     "test1": V1Param(value="wasbs://container@user.blob.core.windows.net/path"),
    >>>     "test2": V1Param(value="wasbs://container@user.blob.core.windows.net/path"),
    >>> }
    ```
    """


class Uri(_Uri):
    """Uri type.

    Args:
        user: str
        password: str
        host: str

    ### YAML usage

    The inputs definition

    ```yaml
    >>> inputs:
    >>>   - name: test1
    >>>     type: uri
    >>>   - name: test2
    >>>     type: uri
    ```

    The params usage

    ```yaml
    >>> params:
    >>>   test1: {value: "https://username1:password1@service.com"}
    >>>   test1: {value: "https://username2:password2@service.com"}
    ```

    ### Python usage

    The inputs definition

    ```python
    >>> from polyaxon import types
    >>> from polyaxon.schemas import V1IO
    >>> inputs = [
    >>>     V1IO(
    >>>         name="test1",
    >>>         type=types.URI,
    >>>     ),
    >>> ]
    ```

    The params usage

    ```python
    >>> from polyaxon.schemas import V1Param
    >>> params = {
    >>>     "test1": V1Param(value="https://username2:password2@service.com"),
    >>> }
    ```

    > Normally you should not be passing auth details in plain values.
    """


# Backwards compatibility
V1GcsType = GcsPath
V1S3Type = S3Path
V1UriType = Uri
V1WasbType = WasbPath
