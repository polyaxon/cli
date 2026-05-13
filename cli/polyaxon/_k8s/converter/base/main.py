from typing import Dict, Iterable, List, Optional

from clipped.utils.lists import to_list
from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._env_vars.keys import ENV_KEYS_SANDBOX_TOKEN
from polyaxon._flow import V1Init, V1Plugins
from polyaxon._k8s import k8s_schemas
from polyaxon._runner.converter import BaseConverter as _BaseConverter
from polyaxon._sandbox.auth import derive_sandbox_token_from_env
from polyaxon._sandbox.constants import SANDBOX_BOOTSTRAP_PATH, SANDBOX_PORT
from polyaxon.exceptions import PolyaxonConverterError


class MainConverter(_BaseConverter):
    def _get_main_container(
        self,
        container_id: str,
        main_container: k8s_schemas.V1Container,
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
    ) -> k8s_schemas.V1Container:
        connections = connections or []
        connection_by_names = connection_by_names or {}
        secrets = secrets or []
        config_maps = config_maps or []

        if artifacts_store and not run_path:
            raise PolyaxonConverterError("Run path is required for main container.")

        if plugins and plugins.sandbox:
            if not main_container:
                raise PolyaxonConverterError(
                    "plugins.sandbox requires a main container."
                )
            if main_container.args and not main_container.command:
                raise PolyaxonConverterError(
                    "plugins.sandbox does not support args without command."
                )
            user_argv = to_list(main_container.command, check_none=True) + to_list(
                main_container.args, check_none=True
            )
            main_container.command = [SANDBOX_BOOTSTRAP_PATH]
            main_container.args = user_argv

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

        # Mounts
        volume_mounts = (
            self._get_mounts(
                use_auth_context=plugins.auth,
                use_artifacts_context=False,  # Main container has a check and handling for this
                use_docker_context=plugins.docker,
                use_shm_context=plugins.shm,
                use_tmux_context=plugins.tmux,
                use_sandbox_context=plugins.sandbox,
                run_path=run_path,
            )
            if plugins
            else []
        )
        volume_mounts = volume_mounts + self._get_main_volume_mounts(
            plugins=plugins,
            init=init,
            connections=requested_connections,
            secrets=requested_secrets,
            config_maps=requested_config_maps,
            run_path=run_path,
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
        if plugins and plugins.sandbox:
            env.append(
                self._get_env_var(
                    name=ENV_KEYS_SANDBOX_TOKEN,
                    value=derive_sandbox_token_from_env(self.run_uuid),
                )
            )
        env += self._get_resources_env_vars(main_container.resources)

        # Env from
        env_from = self._get_env_from_k8s_resources(
            secrets=requested_secrets, config_maps=requested_config_maps
        )

        ports = list(to_list(ports, check_none=True))
        if plugins and plugins.sandbox and SANDBOX_PORT not in ports:
            ports.append(SANDBOX_PORT)

        ports = [k8s_schemas.V1ContainerPort(container_port=port) for port in ports]

        return self._patch_container(
            container=main_container,
            name=container_id,
            env=env,
            env_from=env_from,
            volume_mounts=volume_mounts,
            ports=ports or None,
        )
