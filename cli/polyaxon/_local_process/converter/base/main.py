from typing import Dict, Iterable, List, Optional

from clipped.utils.lists import to_list

from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._flow import V1Init, V1Plugins
from polyaxon._local_process import process_types
from polyaxon._runner.converter import BaseConverter as _BaseConverter
from polyaxon.exceptions import PolyaxonConverterError


class MainConverter(_BaseConverter):
    def _get_main_container(
        self,
        container_id: str,
        main_container: process_types.V1Container,
        plugins: V1Plugins,
        artifacts_store: Optional[V1Connection],
        init: Optional[List[V1Init]],
        connections: Optional[List[str]],
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        run_path: Optional[str],
        kv_env_vars: List[List] = None,
        ports: List[int] = None,
    ) -> process_types.V1Container:
        connections = connections or []
        connection_by_names = connection_by_names or {}
        secrets = secrets or []
        config_maps = config_maps or []

        if artifacts_store and not run_path:
            raise PolyaxonConverterError("Run path is required for main container.")

        if artifacts_store and (
            not plugins.collect_artifacts or plugins.mount_artifacts_store
        ):
            if artifacts_store.name not in connection_by_names:
                connection_by_names[artifacts_store.name] = artifacts_store
            if artifacts_store.name not in connections:
                connections.append(artifacts_store.name)

        requested_connections = [connection_by_names[c] for c in connections]
        requested_config_maps = V1Connection.get_requested_resources(
            resources=config_maps,
            connections=requested_connections,
            resource_key="config_map",
        )
        requested_secrets = V1Connection.get_requested_resources(
            resources=secrets, connections=requested_connections, resource_key="secret"
        )

        # Env vars
        env = self._get_main_env_vars(
            plugins=plugins,
            kv_env_vars=kv_env_vars,
            artifacts_store_name=artifacts_store.name if artifacts_store else None,
            connections=requested_connections,
            secrets=requested_secrets,
            config_maps=requested_config_maps,
        )

        # Env from
        resources = to_list(requested_secrets, check_none=True) + to_list(
            requested_config_maps, check_none=True
        )
        env += self._get_env_from_json_resources(resources=resources)

        return self._patch_container(
            container=main_container,
            name=container_id,
            env=env,
        )
