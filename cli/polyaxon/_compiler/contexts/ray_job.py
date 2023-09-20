import copy

from typing import Dict, Optional

from polyaxon._compiler.contexts.base import BaseContextsManager
from polyaxon._connections import V1Connection
from polyaxon._flow import V1CompiledOperation, V1RayJob, V1RayReplica


class RayJobContextsManager(BaseContextsManager):
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
        job = compiled_operation.run  # type: V1RayJob

        def _get_replica(replica: Optional[V1RayReplica]) -> Dict:
            if not replica:
                return contexts
            return cls._resolver_replica(
                contexts={"globals": copy.copy(contexts["globals"])},
                init=replica.init,
                connections=replica.connections,
                connection_by_names=connection_by_names,
            )

        return {
            "head": _get_replica(job.head),
            "workers": {wn: _get_replica(job.workers[wn]) for wn in job.workers},
        }
