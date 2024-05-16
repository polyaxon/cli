from typing import Dict, Iterable, List, Optional, Union

from polyaxon import settings
from polyaxon._auxiliaries import V1PolyaxonSidecarContainer
from polyaxon._connections import V1Connection, V1ConnectionResource
from polyaxon._flow import V1Environment, V1Init, V1Plugins
from polyaxon._k8s import k8s_schemas
from polyaxon._local_process import process_types
from polyaxon._local_process.converter.base.containers import ContainerMixin
from polyaxon._local_process.converter.base.env_vars import EnvMixin
from polyaxon._local_process.converter.base.init import InitConverter
from polyaxon._local_process.converter.base.main import MainConverter
from polyaxon._local_process.converter.base.mounts import MountsMixin
from polyaxon._runner.converter import BaseConverter as _BaseConverter
from polyaxon._runner.kinds import RunnerKind
from polyaxon.exceptions import PolyaxonConverterError


class BaseConverter(
    MainConverter, InitConverter, ContainerMixin, EnvMixin, MountsMixin, _BaseConverter
):
    RUNNER_KIND = RunnerKind.PROCESS

    @classmethod
    def _get_sidecar_container(
        cls,
        container_id: str,
        polyaxon_sidecar: V1PolyaxonSidecarContainer,
        env: List[process_types.V1EnvVar],
        artifacts_store: V1Connection,
        plugins: V1Plugins,
        run_path: Optional[str],
    ) -> Optional[process_types.V1Container]:
        return None

    @classmethod
    def _k8s_to_process_env_var(
        cls,
        env_var: List[k8s_schemas.V1EnvVar],
    ) -> List[process_types.V1EnvVar]:
        if not env_var:
            return []

        process_env_var = []
        for item in env_var:
            if isinstance(item, dict):
                try:
                    item = k8s_schemas.V1EnvVar(**item)
                except (ValueError, TypeError) as e:
                    raise PolyaxonConverterError(
                        f"Could not parse env var value `{item}` from the K8S schema in container section"
                    ) from e
            process_env_var.append(cls._get_env_var(name=item.name, value=item.value))

        return process_env_var

    @staticmethod
    def _new_container(name: str) -> process_types.V1Container:
        return process_types.V1Container(name=name)

    @classmethod
    def _ensure_container(
        cls,
        container: Union[k8s_schemas.V1Container, process_types.V1Container],
        volumes: List[k8s_schemas.V1Volume],
    ) -> process_types.V1Container:
        if not isinstance(container, k8s_schemas.V1Container):
            return container
        return process_types.V1Container(
            name=container.name,
            command=container.command,
            args=container.args,
            env=cls._k8s_to_process_env_var(container.env),
            working_dir=container.working_dir,
        )

    def get_replica_resource(
        self,
        environment: V1Environment,
        plugins: V1Plugins,
        volumes: List[k8s_schemas.V1Volume],
        init: List[V1Init],
        sidecars: List[k8s_schemas.V1Container],
        container: k8s_schemas.V1Container,
        artifacts_store: V1Connection,
        connections: List[str],
        connection_by_names: Dict[str, V1Connection],
        secrets: Optional[Iterable[V1ConnectionResource]],
        config_maps: Optional[Iterable[V1ConnectionResource]],
        kv_env_vars: List[List],
        default_sa: Optional[str] = None,
        ports: List[int] = None,
    ) -> List[process_types.V1Container]:
        volumes = volumes or []
        init = init or []
        sidecars = sidecars or []
        connections = connections or []
        environment = environment or V1Environment()
        environment.service_account_name = (
            environment.service_account_name
            or default_sa
            or settings.AGENT_CONFIG.runs_sa
        )

        init_connections = self.filter_connections_from_init(init=init)

        init_containers = self.get_init_containers(
            polyaxon_init=self.polyaxon_init,
            plugins=plugins,
            artifacts_store=artifacts_store,
            init_connections=init_connections,
            init_containers=self.filter_containers_from_init(init=init),
            connection_by_names=connection_by_names,
            log_level=plugins.log_level,
            volumes=volumes,
        )

        sidecar_containers = self.get_sidecar_containers(
            polyaxon_sidecar=self.polyaxon_sidecar,
            plugins=plugins,
            artifacts_store=artifacts_store,
            sidecar_containers=sidecars,
            log_level=plugins.log_level,
            volumes=volumes,
        )

        main_container = self.get_main_container(
            main_container=self._ensure_container(container, volumes=volumes),
            plugins=plugins,
            artifacts_store=artifacts_store,
            connections=connections,
            init_connections=init_connections,
            connection_by_names=connection_by_names,
            secrets=secrets,
            config_maps=config_maps,
            ports=ports,
            kv_env_vars=kv_env_vars,
        )

        return init_containers + sidecar_containers + [main_container]
