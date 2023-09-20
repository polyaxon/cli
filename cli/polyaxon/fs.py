from polyaxon._fs.fs import (
    get_artifacts_connection,
    get_fs_from_name,
    get_sync_fs_from_connection,
)
from polyaxon._fs.utils import get_store_path

# Backward compatibility
get_artifacts_connection_type = get_artifacts_connection
