import copy

from typing import Dict, Optional

from polyaxon._compiler.contexts.base import BaseContextsManager
from polyaxon._connections import V1Connection
from polyaxon._flow import V1CompiledOperation, V1RayCluster, V1RayReplica


class RayClusterContextsManager(BaseContextsManager):
    @classmethod
    def resolve(
        cls,
        namespace: str,
        owner_name: str,
        project_name: str,
        run_uuid: str,
        contexts: Dict,
        compiled_operation: V1CompiledOperation,
        connection_by_names: Dict[str, V1Connection],
    ) -> Dict:
        contexts["init"] = {}
        contexts["connections"] = {}
        cluster: V1RayCluster = compiled_operation.run

        def _get_replica(replica: Optional[V1RayReplica]) -> Dict:
            if not replica:
                return contexts
            return cls._resolver_replica(
                contexts={"globals": copy.copy(contexts["globals"])},
                init=replica.init,
                connections=replica.connections,
                connection_by_names=connection_by_names,
            )

        data = {
            "head": _get_replica(cluster.head),
        }
        if cluster.workers:
            data["workers"] = {
                wn: _get_replica(cluster.workers[wn]) for wn in cluster.workers
            }
        return data
