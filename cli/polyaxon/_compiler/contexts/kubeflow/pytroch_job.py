import copy

from typing import Dict, Optional

from polyaxon._compiler.contexts.base import BaseContextsManager
from polyaxon._connections import V1Connection
from polyaxon._flow import V1CompiledOperation, V1KFReplica, V1PytorchJob


class PytorchJobContextsManager(BaseContextsManager):
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
        job = compiled_operation.run  # type: V1PytorchJob

        def _get_replica(replica: Optional[V1KFReplica]) -> Dict:
            if not replica:
                return contexts
            return cls._resolver_replica(
                contexts={"globals": copy.copy(contexts["globals"])},
                init=replica.init,
                connections=replica.connections,
                connection_by_names=connection_by_names,
            )

        return {
            "master": _get_replica(job.master),
            "worker": _get_replica(job.worker),
        }
