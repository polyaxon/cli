import copy
from typing import Dict, Optional

from polyaxon._compiler.contexts.base import BaseContextsManager
from polyaxon._connections import V1Connection
from polyaxon._flow.operations.compiled_operation import V1CompiledOperation
from polyaxon._flow.run.dask.dask import V1DaskCluster
from polyaxon._flow.run.dask.replica import V1DaskReplica


class DaskClusterContextsManager(BaseContextsManager):
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
        cluster: V1DaskCluster = compiled_operation.run

        def _get_replica(replica: Optional[V1DaskReplica]) -> Dict:
            if not replica:
                return contexts
            return cls._resolver_replica(
                contexts={"globals": copy.copy(contexts["globals"])},
                init=replica.init,
                connections=replica.connections,
                connection_by_names=connection_by_names,
            )

        return {
            "worker": _get_replica(cluster.worker),
            "scheduler": _get_replica(cluster.scheduler),
        }
