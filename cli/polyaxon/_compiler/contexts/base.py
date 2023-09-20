from typing import Dict, List

from clipped.utils.lists import to_list

from polyaxon._connections import V1Connection
from polyaxon._flow import V1CompiledOperation, V1Init


class BaseContextsManager:
    @classmethod
    def _resolve_init_contexts(
        cls,
        contexts: Dict,
        init: List[V1Init],
        connection_by_names: Dict[str, V1Connection],
    ):
        init = to_list(init, check_none=True)
        connections = [i.connection for i in init if i.connection]
        return cls._resolve_connections_contexts(
            contexts=contexts,
            connections=connections,
            connection_by_names=connection_by_names,
            key="init",
        )

    @staticmethod
    def _resolve_connections_contexts(
        contexts: Dict,
        connections: List[str],
        connection_by_names: Dict[str, V1Connection],
        key: str = "connections",
    ) -> Dict:
        connections = to_list(connections, check_none=True)
        for connection in connections:
            if connection_by_names[connection].schema_:
                schema_ = connection_by_names[connection].schema_
                if hasattr(schema_, "to_dict"):
                    contexts[key][connection] = schema_.to_dict()
                else:
                    contexts[key][connection] = schema_
            else:
                contexts[key][connection] = {}
        return contexts

    @classmethod
    def _resolver_replica(
        cls,
        contexts: Dict,
        init: List[V1Init],
        connections: List[str],
        connection_by_names: Dict[str, V1Connection],
    ) -> Dict:
        contexts["init"] = {}
        contexts["connections"] = {}
        contexts = cls._resolve_init_contexts(
            contexts=contexts, init=init, connection_by_names=connection_by_names
        )
        contexts = cls._resolve_connections_contexts(
            contexts=contexts,
            connections=connections,
            connection_by_names=connection_by_names,
        )
        return contexts

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
        raise NotImplementedError()
