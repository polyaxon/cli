from typing import Dict, List, Optional

from clipped.utils.lists import to_list

from polyaxon._connections import V1Connection
from polyaxon._flow import V1Init


def get_connection_annotations(
    artifacts_store: Optional[V1Connection],
    init_connections: Optional[List[V1Init]],
    connections: List[str],
    connection_by_names: Optional[Dict[str, V1Connection]],
) -> Dict:
    """Resolve all annotations to inject per replica"""
    connections = to_list(connections, check_none=True)
    init_connections = to_list(init_connections, check_none=True)
    connection_by_names = connection_by_names or {}

    requested_connection_names = connections[:]
    for init_connection in init_connections:
        if (
            init_connection.connection
            and init_connection.connection not in requested_connection_names
        ):
            requested_connection_names.append(init_connection.connection)
    if artifacts_store and artifacts_store.name not in requested_connection_names:
        requested_connection_names.append(artifacts_store.name)

    annotations = {}
    for c in requested_connection_names:
        annotations.update(connection_by_names[c].annotations or {})

    return annotations
